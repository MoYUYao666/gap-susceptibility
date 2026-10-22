"""Paper3 Qwen2-VL — 用 processor messages 格式（和 LLaVA 的唯一区别）"""
import os, sys, json, torch, gc, glob, argparse
import numpy as np
import pandas as pd
from PIL import Image
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--rank', type=int, default=8)
parser.add_argument('--epochs', type=int, default=3)
parser.add_argument('--seed', type=int, default=42)
parser.add_argument('--model-path', type=str, default='/root/qwen2vl_fp16',
                    help='本地模型路径（fp16 原版；bitsandbytes 4bit 加载时自动量化）')
parser.add_argument('--block-config', type=str, default='uniform',
                    choices=['uniform', 'theory', 'violation'],
                    help='theory: shallow(0-7) rank8/其余 rank2; violation: deep(20-27) rank8/其余 rank2; uniform: 全层 rank4')
# --- 云端补强新增（2026-09-13）: 投影器 vs LLM 不对称秩 + 目标模块/批大小控制 ---
parser.add_argument('--attn-targets', type=str, default='qkvo', choices=['qkvo', 'none'],
                    help='注意力 LoRA 目标: qkvo(默认)/none(不加注意力适配器, 配合 --proj-rank 做"仅投影器")')
parser.add_argument('--llm-rank', type=int, default=None,
                    help='覆盖 LLM 侧基础秩(uniform 默认 4; theory/violation 的"其余层"默认 2)')
parser.add_argument('--proj-rank', type=int, default=None,
                    help='投影器(merger)LoRA 秩; 设置后自动把 --proj-targets 加入目标模块')
parser.add_argument('--proj-targets', type=str, default='mlp.0,mlp.2',
                    help='投影器模块后缀(逗号分隔); Qwen2-VL 为 visual.merger.mlp.0/.2, 由日志中的匹配数校验')
parser.add_argument('--batch-size', type=int, default=1, help='训练批大小(默认 1, 与既有协议一致)')
parser.add_argument('--out-dir', type=str, default=None,
                    help='结果 JSON 输出目录(默认 <repo>/paper3/scripts/outputs/experiments)')
parser.add_argument('--tag', type=str, default='', help='文件名附加标签, 避免覆盖既有结果')
parser.add_argument('--image-mode', type=str, default='blank', choices=['blank', 'noise'],
                    help='视觉输入: blank = np.zeros 全黑图, 与 LLaVA 脚本一致且 E0 与 seed 无关(默认); '
                         'noise = np.random.randint 按 seed 播撒的噪声图, 即 2026-09-13 之前的 vintage, '
                         '仅为复现旧结果保留。注意: 两种模式的 E0 不可比。')
args = parser.parse_args()

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def log(msg): print(msg, flush=True)

gc.collect()
torch.manual_seed(args.seed); np.random.seed(args.seed)
log(f"Qwen2-VL | Rank={args.rank} | Seed={args.seed}")

# ==== 1. Data ====
log("\n[1] Data...")
parquet_files = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train-*.parquet"))
if not parquet_files: log("No parquet!"); sys.exit(1)
df = pd.read_parquet(parquet_files[0]); samples = df.head(20).to_dict('records')
log(f"  {len(samples)} samples")

# ==== 2. Model ====
log("\n[2] Model...")
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(args.model_path, quantization_config=quant, device_map="auto")
processor = AutoProcessor.from_pretrained(args.model_path)
log(f"  VRAM: {torch.cuda.memory_allocated()/1e9:.1f} GB")

# ==== 3. LoRA ====
log("\n[3] LoRA...")
from peft import LoraConfig, get_peft_model, TaskType
# --block-config: uniform=全层同 rank(默认); theory=shallow(0-7)高rank/其余低;
#                 violation=deep(20-27)高rank/其余低 (Qwen2-7B 28 层)
bc = getattr(args, 'block_config', 'uniform')
# 注意：peft 用 re.fullmatch 匹配 rank_pattern，模式必须覆盖完整模块名（尾随 .*）。
# 旧版缺少尾随 .* 导致 theory/violation 的 rank_pattern 从未生效（均退化为全层 rank 2）。
if bc == 'theory':
    lora_rank, rank_pattern = 2, {r".*layers\.([0-7])\..*": 8}
elif bc == 'violation':
    lora_rank, rank_pattern = 2, {r".*layers\.(2[0-7])\..*": 8}
else:
    lora_rank, rank_pattern = 4, {}
if args.llm_rank is not None:          # 云端补强: 显式覆盖 LLM 侧基础秩
    lora_rank = int(args.llm_rank)
if args.block_config == 'uniform' and args.llm_rank is None:
    # fix 2026-10-22: --rank was previously only a label; use it as the actual LoRA rank
    lora_rank = int(args.rank)
_attn = ["q_proj", "k_proj", "v_proj", "o_proj"] if args.attn_targets == 'qkvo' else []
_proj_suffixes = [s.strip() for s in args.proj_targets.split(',') if s.strip()]
_targets = list(_attn)
if args.proj_rank is not None:
    _targets += _proj_suffixes
    rank_pattern = dict(rank_pattern)
    rank_pattern[r".*(%s).*" % "|".join(s.replace('.', r'\.') for s in _proj_suffixes)] = int(args.proj_rank)
log(f"  targets={_targets or 'NONE'} proj_rank={args.proj_rank} llm_base_rank={lora_rank}")
if not _targets:
    log("ERROR: no LoRA target modules (attn-targets=none and proj-rank unset)"); sys.exit(2)
peft_cfg = LoraConfig(r=lora_rank, lora_alpha=16, rank_pattern=rank_pattern,
                      target_modules=_targets,
                      lora_dropout=0.1, bias="none", task_type=TaskType.CAUSAL_LM)
model = get_peft_model(model, peft_cfg)
log(f"  Config={bc} rank={lora_rank} pattern={rank_pattern or 'uniform'}")
log(f"  Trainable: {sum(p.numel() for p in model.parameters() if p.requires_grad)/1e6:.1f}M")
if args.proj_rank is not None:
    # 首跑校验: 投影器 LoRA 是否真的匹配到模块(命名不匹配时这里会是 0, 必须排查)
    _hits = [n for n, _ in model.named_modules() if 'lora_A' in n and any(s in n for s in _proj_suffixes)]
    log(f"  projector LoRA modules matched: {len(_hits)} {_hits[:3]}")
    if not _hits:
        log("ERROR: --proj-rank set but no projector module matched -- check --proj-targets"); sys.exit(2)

# ==== 4. Pre-process (Qwen way: messages with image object) ====
log("\n[4] Pre-process...")
if args.image_mode == 'noise':
    # 2026-09-13 之前的 vintage: 每 seed 一张随机噪声图 → E0 随 seed 变化(27008–46592), 仅用于复现
    blank_img = Image.fromarray(np.random.randint(0, 255, (336, 336, 3), dtype=np.uint8))
else:
    # 与 run_training.py(LLaVA) 一致的全黑图 → E0 与 seed 无关, 跨 seed 统计可直接平均
    blank_img = Image.fromarray(np.zeros((336, 336, 3), dtype=np.uint8))
log(f"  visual input: {args.image_mode}"
    + (" (deterministic black image, matches the LLaVA script)" if args.image_mode == 'blank' else ""))
img_tok_id = model.config.image_token_id

processed = []
for s in samples:
    instr = s.get('instruction',''); out = s.get('output','')
    # Qwen2-VL native format
    messages = [
        {"role":"user","content":[{"type":"image","image":blank_img},{"type":"text","text":instr}]},
        {"role":"assistant","content":[{"type":"text","text":out}]},
    ]
    text = processor.apply_chat_template(messages, add_generation_prompt=False)
    proc = processor(text=[text], images=[blank_img], return_tensors="pt", max_length=1024)
    _mm = proc.get("mm_token_type_ids", None)   # transformers>=5 需要, 4.x 无此键
    processed.append({
        "input_ids": proc["input_ids"][0],
        "attention_mask": proc["attention_mask"][0],
        "pixel_values": proc["pixel_values"],
        "image_grid_thw": proc["image_grid_thw"],
        "mm_token_type_ids": (_mm[0] if _mm is not None else None),
        "labels": proc["input_ids"][0].clone(),
    })

train_data, eval_data = processed[4:], processed[:4]
log(f"  Train: {len(train_data)}, Eval: {len(eval_data)}")

# ==== 5. E(0) ====
pad_id = processor.tokenizer.pad_token_id

def compute_E(m, edata, max_n=4):
    m.eval(); total, n = 0.0, 0
    with torch.no_grad():
        for i in range(min(max_n, len(edata))):
            d = edata[i]
            b = {"input_ids": d["input_ids"].unsqueeze(0).cuda(),
                 "attention_mask": d["attention_mask"].unsqueeze(0).cuda(),
                 "pixel_values": d["pixel_values"].cuda(),
                 "image_grid_thw": d["image_grid_thw"].cuda()}
            if d.get("mm_token_type_ids") is not None:
                b["mm_token_type_ids"] = d["mm_token_type_ids"].unsqueeze(0).cuda()
            out = m(**b, output_hidden_states=True)
            hidden = out.hidden_states[-1][0]; ids = b["input_ids"][0]
            v_mask = (ids == img_tok_id)
            l_mask = (ids != img_tok_id) & (ids != pad_id)
            if v_mask.sum()>0 and l_mask.sum()>0:
                hv = hidden[v_mask].mean(0); hl = hidden[l_mask].mean(0)
                total += ((hv-hl)**2).sum().item(); n += 1
    m.train()
    return total/max(n,1), n

E0, n0 = compute_E(model, eval_data)
log(f"  E(0)={E0:.1f} (n={n0})")

# ==== 6. Training ====
log(f"\n[6] Training {args.epochs} epochs...")
from torch.utils.data import DataLoader, Dataset
class ListDS(Dataset):
    def __init__(self,d): self.data=d
    def __len__(self): return len(self.data)
    def __getitem__(self,i): return self.data[i]

def collate(batch, max_len=1024):
    import torch.nn.functional as F
    def pad2d(t,v,L): need=max(0,L-t.size(0)); return F.pad(t,(0,need),value=v) if need>0 else t[:L]
    ids = torch.stack([pad2d(b["input_ids"],0,max_len) for b in batch])
    att = torch.stack([pad2d(b["attention_mask"],0,max_len) for b in batch])
    pix = torch.cat([b["pixel_values"] for b in batch], dim=0)
    gthw = torch.cat([b["image_grid_thw"] for b in batch], dim=0)
    lbl = torch.stack([pad2d(b["labels"],-100,max_len) for b in batch]); lbl[att==0] = -100
    out = {"input_ids":ids,"attention_mask":att,"pixel_values":pix,"image_grid_thw":gthw,"labels":lbl}
    if batch[0].get("mm_token_type_ids") is not None:
        out["mm_token_type_ids"] = torch.stack([pad2d(b["mm_token_type_ids"],0,max_len) for b in batch])
    return out

loader = DataLoader(ListDS(train_data), batch_size=max(1, int(args.batch_size)), shuffle=True, collate_fn=collate)
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=5e-5)
start = datetime.now()
energy_history = [E0]

for epoch in range(args.epochs):
    model.train(); total_loss, n_valid = 0.0, 0
    for step, batch in enumerate(loader):
        batch = {k:v.cuda() for k,v in batch.items() if v is not None}
        out = model(**batch); loss = out.loss
        if torch.isnan(loss) or torch.isinf(loss): continue
        loss.backward(); total_loss += loss.item(); n_valid += 1
    if n_valid>0: opt.step()
    opt.zero_grad()
    log(f"  Ep{epoch+1}: loss={total_loss/max(n_valid,1):.4f} ({n_valid})")
    Et, nt = compute_E(model, eval_data)
    energy_history.append(Et)
    log(f"  E({epoch+1})={Et:.1f} {'↓' if Et<energy_history[-2] else '↑'}")

elapsed = (datetime.now()-start).total_seconds()
Et0,Etf = energy_history[0], energy_history[-1]
log(f"\nE: {' -> '.join([f'{e:.0f}' for e in energy_history])}")
log(f"DeltaE: {Etf-Et0:+.0f} ({(Etf/Et0-1)*100:+.1f}%), {elapsed:.0f}s")

# 保存结果 json（默认写入 repo 的 experiments 目录；命名兼容旧结果 + 可选标签）
bc = getattr(args, 'block_config', 'uniform')
_out = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "experiments")
os.makedirs(_out, exist_ok=True)
_extra = []
if args.attn_targets != 'qkvo':
    _extra.append('t' + args.attn_targets)
if args.proj_rank is not None:
    _extra.append('pr%d' % args.proj_rank)
if args.llm_rank is not None:
    _extra.append('lr%d' % args.llm_rank)
if args.batch_size != 1:
    _extra.append('b%d' % args.batch_size)
if args.tag:
    _extra.append(args.tag)
_fname = f"qwen_cf_{bc}_rank{args.rank}_seed{args.seed}" + (('_' + '_'.join(_extra)) if _extra else '') + ".json"
save_path = os.path.join(_out, _fname)
with open(save_path, 'w', encoding='utf-8') as f:
    json.dump({
        "name": f"qwen_cf_r{args.rank}_s{args.seed}",
        "rank": args.rank,
        "seed": args.seed,
        "epochs": args.epochs,
        "model_path": args.model_path,
        "block_config": bc,
        "attn_targets": args.attn_targets,
        "llm_rank": args.llm_rank,
        "proj_rank": args.proj_rank,
        "proj_targets": _proj_suffixes if args.proj_rank is not None else None,
        "batch_size": args.batch_size,
        "image_mode": args.image_mode,
        "trainable_params": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
        "E": energy_history,
        "delta_E": float(Etf - Et0),
        "ok": True,
    }, f, indent=2)
log(f"Saved: {save_path}")
log("DONE")
