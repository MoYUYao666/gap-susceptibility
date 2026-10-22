"""Paper3 训练脚本 — 完全独立，无项目 import。

直接从 parquet 加载 Alpaca 数据，加载 LLaVA，训练，测 E(t)。
"""
import os, sys, json, torch, gc, glob, argparse, time
import numpy as np
import pandas as pd
from PIL import Image
from datetime import datetime

# CLI: python run_training.py --rank 4
parser = argparse.ArgumentParser()
parser.add_argument('--rank', type=int, default=8)
parser.add_argument('--epochs', type=int, default=1)
parser.add_argument('--seed', type=int, default=42)
parser.add_argument('--num-samples', type=int, default=20)
parser.add_argument('--lr', type=float, default=5e-5)
parser.add_argument('--warmup', action='store_true', default=False)
parser.add_argument('--data-path', type=str, default=None,
                    help='自定义数据集 parquet 路径（默认找 train-*.parquet）')
parser.add_argument('--model-path', type=str, default=None,
                    help='本地模型目录（默认 llava-hf 在线）')
parser.add_argument('--compute-dtype', type=str, default='float16', choices=['float16', 'bfloat16'],
                    help='4-bit 量化计算精度（float16 默认 / bfloat16 消融）')
parser.add_argument('--opt', type=str, default='adamw', choices=['adamw', 'sgd'],
                    help='优化器（adamw 默认 / sgd 消融）')
parser.add_argument('--images-dir', type=str, default=None,
                    help='(可选) 真实图像目录; parquet 需含 image 列(文件名)。默认空白图协议。')
parser.add_argument('--lang-only', action='store_true', default=False,
                    help='机制干预: 损失仅计算语言 token 位置(图像 token 位置 labels=-100)')
parser.add_argument('--target-proj', action='store_true', default=False,
                    help='机制探查: 将 LoRA 目标扩展到多模态投影器(linear_1/linear_2), 其余同 uniform')
parser.add_argument('--rank-vision', type=int, default=None, help='explicit vision-tower rank (custom block config)')
parser.add_argument('--rank-shallow', type=int, default=None, help='explicit LLM shallow-block rank (layers 0-7)')
parser.add_argument('--rank-mid', type=int, default=None, help='explicit LLM mid-block rank (layers 8-23)')
parser.add_argument('--rank-deep', type=int, default=None, help='explicit LLM deep-block rank (layers 24-31)')
parser.add_argument('--block-config', type=str, default='uniform',
                    choices=['uniform', 'uniformv1', 'exp', 'greedy', 'expnorm', 'deepavoid'],
                    help='块级秩分配(预算匹配): uniform=全层 r4(含 vision); uniformv1=LLM 全层 r4 但 vision r1'
                         '(与各策略的 vision r1 口径一致, 消除 vision 秩混淆); '
                         'exp(beta*=1/sigma, LLM 块按份额): shallow(0-7) r9 / mid(8-23) r1 / deep(24-31) r6; '
                         'greedy: shallow r16 / mid r1 / deep r1 (被排块 rank>=1 下限, 预算开销披露)。'
                         'expnorm=按参数量归一化的 beta* 份额 (11/1/4); deepavoid=层剖面驱动(4/6/1)。')
parser.add_argument('--grad-mask', type=str, default='none', choices=['none', 'image', 'text'],
                    help='机制干预(Tier A2): 在首个 LLM 解码层入口按 token 位置切断梯度通路'
                         '(前向不变, 仅梯度门控): image=图像 token 位置(/切片 0:576)不再回传梯度; '
                         'text=语言 token 位置不再回传梯度。')
parser.add_argument('--lora-alpha', type=float, default=None,
                    help='LoRA alpha 消融(Tier A7); 缺省时保持参考行为(uniform: r*2; 块策略: 16)')
parser.add_argument('--attn-targets', type=str, default='qkvo', choices=['qkvo', 'q', 'qv', 'qo', 'none'],
                    help='注意力目标模块消融(Tier A7): qkvo(默认) / q / qv / qo / none(不加注意力 LoRA, 配合 --proj-rank 做投影器单独控制)')
parser.add_argument('--batch-size', type=int, default=1,
                    help='训练批大小(Tier A7; 参考协议为 1)')
parser.add_argument('--proj-rank', type=int, default=None,
                    help='投影器 LoRA 秩(Tier A6): 设置后投影器使用该秩(可与 --rank 不对称), '
                         '并自动把 linear_1/linear_2 加入目标模块')
parser.add_argument('--save-adapter-dir', type=str, default=None,
                    help='optional: save the trained LoRA adapter here (downstream checks)')
parser.add_argument('--data-offset', type=int, default=0,
                    help='样本窗口起点(Tier A3/A4): 从 parquet 第 offset 行开始取 num_samples 个样本, '
                         '用于产生独立批次')
args = parser.parse_args()

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

def log(msg):
    print(msg, flush=True)

gc.collect()
torch.manual_seed(args.seed)
np.random.seed(args.seed)
log(f"Seed: {args.seed}")
log("=" * 50)
log("Paper3 Training Pipeline")
log("=" * 50)

# ==== 1. Load Alpaca data (CPU first!) ====
log("\n[1] Loading Alpaca data...")
if args.data_path:
    parquet_files = [args.data_path]
else:
    parquet_files = glob.glob(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "train-*.parquet"
    ))
if not parquet_files:
    log("ERROR: No parquet file found!")
    sys.exit(1)

df = pd.read_parquet(parquet_files[0])
n_total = args.num_samples  # train + eval
_off = max(0, int(args.data_offset))
samples = df.iloc[_off:_off + n_total].to_dict('records')
log(f"  Loaded {len(samples)} samples (offset={_off})")

# Format as conversations
def fmt_conv(inst, inp, out):
    return [
        {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": inst + ('\n' + inp if inp else '')}]},
        {"role": "assistant", "content": [{"type": "text", "text": out}]},
    ]

formatted = []
for s in samples:
    formatted.append({
        'instruction': s.get('instruction', ''),
        'input': s.get('input', ''),
        'output': s.get('output', ''),
        'image': s.get('image', ''),
        'conversation': fmt_conv(s.get('instruction', ''), s.get('input', ''), s.get('output', '')),
    })
log(f"  Formatted {len(formatted)} conversations")

# ==== 2. Load LLaVA ====
log("\n[2] Loading LLaVA-1.5-7B (4-bit)...")
from transformers import LlavaForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
quant = BitsAndBytesConfig(load_in_4bit=True,
                           bnb_4bit_compute_dtype=getattr(torch, args.compute_dtype),
                           bnb_4bit_use_double_quant=True)
model_path = args.model_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "models", "llava-hf")
model = LlavaForConditionalGeneration.from_pretrained(
    model_path, quantization_config=quant, device_map="auto")
processor = AutoProcessor.from_pretrained(model_path)
log(f"  Model loaded. VRAM: {torch.cuda.memory_allocated()/1e9:.1f} GB")

# ==== 3. Apply LoRA ====
log("\n[3] Applying LoRA...")
from peft import LoraConfig, get_peft_model, TaskType
# 块级秩分配: rank_pattern 锚定 language_model.layers.N (避免匹配 vision encoder.layers.N)
_bc = getattr(args, 'block_config', 'uniform')
if args.rank_vision is not None:
    # explicit four-block allocation (NTK / arbitrary baseline arms)
    _pat = {r".*vision_tower.*": args.rank_vision,
            r".*language_model\.layers\.([0-7])\..*": args.rank_shallow if args.rank_shallow is not None else 1,
            r".*language_model\.layers\.([89]|1[0-9]|2[0-3])\..*": args.rank_mid if args.rank_mid is not None else 1,
            r".*language_model\.layers\.(2[4-9]|3[01])\..*": args.rank_deep if args.rank_deep is not None else 1}
    _base_rank, _lora_alpha = 1, 16
elif _bc == 'uniformv1':
    # A5 对照臂: LLM 全层保持 base rank(=4), 仅把 vision 塔压到 r1 —— 与 exp/greedy/expnorm/deepavoid
    # 各策略的 "vision adapters r=1" 口径一致, 消除 vision 秩混淆(base rank 之外的模块仍用 args.rank)
    _pat = {r".*vision_tower.*": 1}
    _base_rank, _lora_alpha = args.rank, args.rank * 2
elif _bc == 'exp':
    _pat = {r".*language_model\.layers\.([0-7])\..*": 9,
            r".*language_model\.layers\.([89]|1[0-9]|2[0-3])\..*": 1,
            r".*language_model\.layers\.(2[4-9]|3[01])\..*": 6,
            r".*vision_tower.*": 1}
    _base_rank, _lora_alpha = 1, 16
elif _bc == 'greedy':
    _pat = {r".*language_model\.layers\.([0-7])\..*": 16,
            r".*language_model\.layers\.([89]|1[0-9]|2[0-3])\..*": 1,
            r".*language_model\.layers\.(2[4-9]|3[01])\..*": 1,
            r".*vision_tower.*": 1}
    _base_rank, _lora_alpha = 1, 16
elif _bc == 'expnorm':
    # Tier A5: beta* 份额在"按块参数量归一化"的 |Gamma| 上重算(LLM 三层块 8/16/8 层,
    # 块参数质量 ∝ 层数; |Gamma|=1614/8717/2727 → 归一化 202/545/341, sigma=141, beta*=0.0071)
    # 目标份额 0.685/0.060/0.255 → 预算 136 rank-layers 下的最优整数实现 11/1/4 (与 exp 同预算)
    _pat = {r".*language_model\.layers\.([0-7])\..*": 11,
            r".*language_model\.layers\.([89]|1[0-9]|2[0-3])\..*": 1,
            r".*language_model\.layers\.(2[4-9]|3[01])\..*": 4,
            r".*vision_tower.*": 1}
    _base_rank, _lora_alpha = 1, 16
elif _bc == 'deepavoid':
    # Tier A5: 遵从 raw 全参数化层剖面(shallow/mid/deep 层均 |Gamma| = 0.31/0.13/4.09,
    # deep 最耦合)的 beta* 份额 → 把容量从 deep 移开; 预算 136 下最优整数实现 4/6/1
    _pat = {r".*language_model\.layers\.([0-7])\..*": 4,
            r".*language_model\.layers\.([89]|1[0-9]|2[0-3])\..*": 6,
            r".*language_model\.layers\.(2[4-9]|3[01])\..*": 1,
            r".*vision_tower.*": 1}
    _base_rank, _lora_alpha = 1, 16
else:
    _pat, _base_rank, _lora_alpha = {}, args.rank, args.rank * 2
if args.proj_rank is not None:
    _pat = dict(_pat)
    _pat[r".*multi_modal_projector.*"] = int(args.proj_rank)
if args.lora_alpha is not None:
    _lora_alpha = float(args.lora_alpha)
_attn = {'qkvo': ["q_proj", "k_proj", "v_proj", "o_proj"],
         'q': ["q_proj"],
         'qv': ["q_proj", "v_proj"],
         'qo': ["q_proj", "o_proj"],
         'none': []}[args.attn_targets]
_targets = list(_attn)
if getattr(args, 'target_proj', False) or args.proj_rank is not None:
    _targets += ["linear_1", "linear_2"]
peft_cfg = LoraConfig(r=_base_rank, lora_alpha=_lora_alpha, rank_pattern=_pat,
                      target_modules=_targets,
                      lora_dropout=0.1, bias="none", task_type=TaskType.CAUSAL_LM)
model = get_peft_model(model, peft_cfg)
n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
_tr = {'vision': 0, 'proj': 0, 'llm': 0}
for _n, _p in model.named_parameters():
    if not _p.requires_grad:
        continue
    _k = 'vision' if 'vision_tower' in _n else ('proj' if 'multi_modal_projector' in _n else 'llm')
    _tr[_k] += _p.numel()
log(f"  LoRA applied (config={args.block_config}, targets={args.attn_targets}, alpha={_lora_alpha:g}, "
    f"proj_rank={args.proj_rank}). Trainable: {n_trainable/1e6:.2f}M "
    f"(llm {_tr['llm']/1e6:.2f}M / vision {_tr['vision']/1e6:.2f}M / proj {_tr['proj']/1e6:.3f}M)")

# ==== 3b. 梯度通路门控 (Tier A2 机制干预) ====
# 在首个 LLM 解码层入口按 token 位置切断梯度: 前向数值不变, 仅把被选位置的通路梯度置零。
_grad_mask = getattr(args, 'grad_mask', 'none')
_hook_handle = None
if _grad_mask != 'none':
    _lm0 = None
    for _n, _m in model.named_modules():
        if _n.endswith('language_model.layers.0'):
            _lm0 = _m
            break
    if _lm0 is None:
        log("ERROR: first LLM decoder layer not found for --grad-mask")
        sys.exit(2)

    def _gate_hook(module, hargs, hkwargs):
        hs = hargs[0] if hargs else hkwargs.get('hidden_states')
        if hs is None or hs.dim() != 3:
            return None
        L = hs.size(1)
        gate = torch.ones(1, L, 1, device=hs.device, dtype=hs.dtype)
        if _grad_mask == 'image':
            gate[:, :576] = 0
        else:
            gate[:, 576:] = 0
        hs_new = hs * gate + hs.detach() * (1.0 - gate)
        if hargs:
            return (hs_new,) + tuple(hargs[1:]), hkwargs
        hkwargs = dict(hkwargs)
        hkwargs['hidden_states'] = hs_new
        return hargs, hkwargs

    _hook_handle = _lm0.register_forward_pre_hook(_gate_hook, with_kwargs=True)
    log(f"  [grad-mask={_grad_mask}] gradient gate on {type(_lm0).__name__} "
        f"({'image' if _grad_mask == 'image' else 'text'} token positions)")

# ==== 4. Pre-process ====
log("\n[4] Pre-processing samples...")
blank_img = Image.fromarray(np.zeros((336, 336, 3), dtype=np.uint8))
pixel_vals = processor.image_processor(blank_img, return_tensors="pt")["pixel_values"]
img_tok = model.config.image_token_index
img_tok_id = img_tok if isinstance(img_tok, int) else img_tok.item()

processed = []
for si, s in enumerate(formatted):
    text = f"USER: {s['instruction']}\nASSISTANT: {s['output']}"
    toks = processor.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    # 576 image tokens + text tokens (skip BOS)
    img_tokens = torch.full((1, 576), img_tok_id, dtype=torch.long)
    input_ids = torch.cat([img_tokens, toks["input_ids"][:, 1:]], dim=1)
    att_mask = torch.cat([torch.ones(1, 576, dtype=torch.long), toks["attention_mask"][:, 1:]], dim=1)
    if args.images_dir:
        img = Image.open(os.path.join(args.images_dir, s.get('image', '')))
        pv = processor.image_processor(img, return_tensors="pt")["pixel_values"].squeeze(0)
    else:
        pv = pixel_vals.squeeze(0)
    processed.append({
        "input_ids": input_ids[0],
        "attention_mask": att_mask[0],
        "pixel_values": pv,
        "labels": input_ids[0].clone(),
    })
    if getattr(args, 'lang_only', False):
        # 机制干预: 图像 token 位置不参与 LM loss → 梯度仅来自语言侧
        processed[-1]["labels"][:576] = -100

train_data = processed[4:]   # skip first 4 for eval
eval_data = processed[:4]
log(f"  Train: {len(train_data)}, Eval: {len(eval_data)}")

# ==== 5. E(0) computation ====
log("\n[5] Computing E(0)...")

def compute_E(m, edata, pad_id, max_n=4):
    m.eval()
    total, n = 0.0, 0
    with torch.no_grad():
        for i in range(min(max_n, len(edata))):
            d = edata[i]
            b = {k: v.unsqueeze(0).cuda() for k, v in d.items()
                 if k in ("input_ids", "attention_mask", "pixel_values")}
            out = m(**b, output_hidden_states=True)
            hidden = out.hidden_states[-1][0]
            ids = b["input_ids"][0]
            v_mask = torch.zeros_like(ids, dtype=torch.bool); v_mask[:576] = True
            l_mask = torch.zeros_like(ids, dtype=torch.bool); l_mask[576:] = (ids[576:] != pad_id)
            if v_mask.sum() > 0 and l_mask.sum() > 0:
                hv = hidden[v_mask].mean(0); hl = hidden[l_mask].mean(0)
                total += ((hv - hl) ** 2).sum().item(); n += 1
    m.train()
    return total / max(n, 1), n

pad_id = processor.tokenizer.pad_token_id
E0, n0 = compute_E(model, eval_data, pad_id)
log(f"  E(0) = {E0:.1f} (n={n0})")

# ==== 6. Training ====
log(f"\n[6] Training {args.epochs} epoch(s)...")
from torch.utils.data import DataLoader, Dataset

class ListDS(Dataset):
    def __init__(self, d): self.data = d
    def __len__(self): return len(self.data)
    def __getitem__(self, i): return self.data[i]

def collate(batch, max_len=1024):
    import torch.nn.functional as F
    def pad2d(t, v, L):
        need = max(0, L - t.size(0))
        return F.pad(t, (0, need), value=v) if need > 0 else t[:L]
    ids = torch.stack([pad2d(b["input_ids"], 0, max_len) for b in batch])
    att = torch.stack([pad2d(b["attention_mask"], 0, max_len) for b in batch])
    pix = torch.stack([b["pixel_values"] for b in batch])
    lbl = torch.stack([pad2d(b["labels"], -100, max_len) for b in batch])
    lbl[att == 0] = -100
    return {"input_ids": ids, "attention_mask": att, "pixel_values": pix, "labels": lbl}

loader = DataLoader(ListDS(train_data), batch_size=max(1, int(args.batch_size)), shuffle=True, collate_fn=collate)
_opt_params = [p for p in model.parameters() if p.requires_grad]
if args.opt == 'sgd':
    # SGD 消融: 动量 0.9, lr 由 --lr 显式指定 (可与 AdamW 同为 5e-5 以做优化器单变量对比)
    opt = torch.optim.SGD(_opt_params, lr=args.lr, momentum=0.9)
else:
    opt = torch.optim.AdamW(_opt_params, lr=args.lr)  # lower lr for fp16 stab
_ws = max(1, len(loader) // 10) if args.warmup else 0
from torch.optim.lr_scheduler import LambdaLR
_warm = LambdaLR(opt, lr_lambda=lambda s: min(1.0, (s + 1) / _ws)) if _ws else None

start = datetime.now()

energy_history = [E0]  # E(0) as baseline
gradnorm_history = []  # Tier A10: 每 epoch 的路由梯度范数 (vision / proj / llm)
# 预先按路由缓存可训练参数, 用 foreach_norm 批量求范数(避免每步数百次同步)
_route_lists = {'vision': [], 'proj': [], 'llm': []}
for _n, _p in model.named_parameters():
    if not _p.requires_grad:
        continue
    _k = 'vision' if 'vision_tower' in _n else ('proj' if 'multi_modal_projector' in _n else 'llm')
    _route_lists[_k].append(_p)

# Train for N epochs, compute E(t) per epoch
for epoch in range(args.epochs):
    model.train()
    total_loss, n_valid = 0.0, 0
    _gn_sum = {k: torch.zeros((), device='cuda') for k in _route_lists}
    _gn_n = 0
    for step, batch in enumerate(loader):
        _t_step = time.time()
        batch = {k: v.cuda() for k, v in batch.items()}
        out = model(**batch)
        loss = out.loss
        if torch.isnan(loss) or torch.isinf(loss):
            continue
        loss.backward()
        # 路由梯度范数(L2): 每路由一次 foreach_norm, 全程无 host 同步
        for _k, _pl in _route_lists.items():
            if not _pl:
                continue
            _gs = [p.grad for p in _pl if p.grad is not None]
            if _gs:
                _gn_sum[_k] = _gn_sum[_k] + torch.stack(torch._foreach_norm(_gs)).pow(2).sum()
        _gn_n += 1
        total_loss += loss.item()
        n_valid += 1
        if step % 4 == 0 or step == len(loader) - 1:
            log(f"    step {step+1}/{len(loader)} loss={loss.item():.4f} "
                f"({time.time()-_t_step:.1f}s/step)")
    if n_valid > 0:
        opt.step()
        if _warm is not None:
            _warm.step()
    opt.zero_grad()
    avg_loss = total_loss / max(n_valid, 1)
    if _gn_n:
        gradnorm_history.append({k: float(v.sqrt().item() / _gn_n) for k, v in _gn_sum.items()})
    log(f"  Epoch {epoch+1}: avg_loss={avg_loss:.4f} ({n_valid}/{len(loader)} valid)"
        + (f" | ||g|| vis={float(_gn_sum['vision'].sqrt().item())/max(_gn_n,1):.3g}"
           f" proj={float(_gn_sum['proj'].sqrt().item())/max(_gn_n,1):.3g}"
           f" llm={float(_gn_sum['llm'].sqrt().item())/max(_gn_n,1):.3g}" if _gn_n else ""))

    Et, nt = compute_E(model, eval_data, pad_id)
    energy_history.append(Et)
    log(f"  E({epoch+1}) = {Et:.1f} (n={nt}) {'↓' if Et < energy_history[-2] else '↑'}")
    # 每 epoch 落盘一次(防后续 epoch OOM/发散导致整轮白跑); 文件名带 _partial, 不参与后续分析
    try:
        _pdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "experiments")
        os.makedirs(_pdir, exist_ok=True)
        _pname = "verify_r%d_s%d_%s_partial.json" % (
            args.rank, args.seed,
            ("b%d" % args.batch_size) if args.batch_size != 1 else "b1")
        with open(os.path.join(_pdir, _pname), "w", encoding="utf-8") as _pf:
            json.dump({"name": f"verify_r{args.rank}_s{args.seed}", "rank": args.rank, "seed": args.seed,
                       "batch_size": args.batch_size, "epochs_target": args.epochs,
                       "epochs_done": epoch + 1, "E": energy_history, "partial": True}, _pf, indent=2)
    except Exception as _e:  # noqa: BLE001
        log(f"  (partial save failed: {_e!r})")

elapsed = (datetime.now() - start).total_seconds()

# ==== DONE ====
Et0, Etf = energy_history[0], energy_history[-1]
E_traj = " → ".join([f"{e:.1f}" for e in energy_history])
log(f"\n{'='*50}")
log(f"E trajectory: {E_traj}")
log(f"Change: {Etf-Et0:+.1f} ({(Etf/Et0-1)*100:+.1f}%)")
log(f"Training time: {elapsed:.0f}s")
log(f"SUCCESS!")
log(f"{'='*50}")

# ==== optional: save adapter for downstream evaluation ====
if getattr(args, 'save_adapter_dir', None):
    try:
        os.makedirs(args.save_adapter_dir, exist_ok=True)
        model.save_pretrained(args.save_adapter_dir)
        log(f'  adapter saved -> {args.save_adapter_dir}')
    except Exception as _e:  # noqa: BLE001
        log(f'  adapter save failed: {_e!r}')

# ==== 保存结果 JSON（供审计对比）====
save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "experiments")
os.makedirs(save_dir, exist_ok=True)
_tag = '' if (args.lr == 5e-5 and not args.warmup and args.compute_dtype == 'float16' and args.opt == 'adamw' and not args.images_dir and not args.data_path and args.epochs == 3 and args.block_config == 'uniform' and not getattr(args, 'lang_only', False) and not getattr(args, 'target_proj', False) and args.grad_mask == 'none' and args.lora_alpha is None and args.attn_targets == 'qkvo' and args.batch_size == 1 and args.proj_rank is None and args.data_offset == 0) \
    else '_lr%g_%s_%s_%s%s%s_e%d_bc%s%s%s%s%s%s%s%s%s' % (args.lr, 'w' if args.warmup else 'nw', args.compute_dtype[:6], args.opt,
                                              '_imgs' if args.images_dir else '',
                                              '_cap' if args.data_path and 'caption' in args.data_path else '',
                                              args.epochs, args.block_config,
                                              '_lang' if getattr(args, 'lang_only', False) else '',
                                              '_proj' if getattr(args, 'target_proj', False) else '',
                                              '' if args.grad_mask == 'none' else '_gm' + args.grad_mask,
                                              '' if args.lora_alpha is None else '_a%g' % args.lora_alpha,
                                              '' if args.attn_targets == 'qkvo' else '_t' + args.attn_targets,
                                              '' if args.batch_size == 1 else '_b%d' % args.batch_size,
                                              '' if args.proj_rank is None else '_pr%d' % args.proj_rank,
                                              '' if args.data_offset == 0 else '_o%d' % args.data_offset)
if getattr(args, "rank_vision", None) is not None:
    _tag = "_bcexplicit_v%d_s%d_m%d_d%d" % (args.rank_vision, args.rank_shallow or 1, args.rank_mid or 1, args.rank_deep or 1)
save_path = os.path.join(save_dir, f"verify_r{args.rank}_s{args.seed}{_tag}.json")
with open(save_path, 'w', encoding='utf-8') as f:
    json.dump({"name": f"verify_r{args.rank}_s{args.seed}" + _tag, "rank": args.rank,
               "seed": args.seed, "epochs": args.epochs, "num_samples": args.num_samples,
               "lr": args.lr, "warmup": args.warmup, "compute_dtype": args.compute_dtype, "opt": args.opt,
               "block_config": args.block_config, "grad_mask": args.grad_mask,
               "lora_alpha": _lora_alpha, "attn_targets": args.attn_targets,
               "batch_size": args.batch_size, "proj_rank": args.proj_rank,
               "data_offset": args.data_offset, "target_proj": bool(getattr(args, 'target_proj', False)),
               "lang_only": bool(getattr(args, 'lang_only', False)),
               "trainable": _tr, "grad_norms": gradnorm_history,
               "E": energy_history, "delta_E": Etf - Et0, "ok": True}, f, indent=2)
log(f"Saved: {save_path}")
