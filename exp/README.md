# 补实验 — 命令行速查

## 🔴 模型获取规则（用户明确要求）

**所有模型一律直接在服务器下载（ModelScope / HF 镜像），禁止"本地下载 → 上传服务器"。**

```bash
# ModelScope（推荐）：
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2-VL-7B-Instruct', local_dir='/root/qwen2vl_fp16')"

# HF 镜像（备用）：
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
```

## 主线

**模型**：llava-hf（必须，vocab=32064 才能用 image_token_index=32000）
**脚本**：exp/ 全部就绪（含 make_dataset.py 数据集转换）

## 进度

- [x] 实验 1（Γ）✅ 已写入 Paper 3 附录（mid 主导 41.2%，vis 负耦合）
- [x] 实验 2（ERS 1-epoch）✅ 已写入 Paper 3（r64 翻转 +151.7，无 plateau 诚实报告）
- [x] 实验 3（ShareGPT）✅ 已写入 Paper 3（r_c∈[5,6] 双数据集复现）
- [x] 实验 4（Qwen）✅ 完成（2026-08-05）——fp16 完整版 + 4bit bnb 加载；Γ 全负；counterfactual rank 不敏感（p=0.95）→ 已写入 Paper 3 Finding 4（C4 验证）
- [x] 实验 5a（OpenCLIP）✅ 已写入 Paper A（R²=0.943, α=-0.002, β=0.484）
- [x] 实验 5b（BitFit）✅ 已写入 Paper A（β≈0 边界案例）

## 实验命令

### 实验 1：Γ 测量（多 rank 多 batch，~30min）

```bash
cd /root/autodl-tmp/work
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
python exp/run_gamma_llava.py --ranks 4,8,16,32,64 --batches 5 --model-path /root/autodl-tmp/llava-hf
```

### 实验 2：ERS 1-epoch（4 ranks × 3 seeds，~1h）

```bash
python exp/run_ers_1epoch.py --model-path /root/autodl-tmp/llava-hf
```

### 实验 3：第二数据集相变（~4h）

```bash
# 1. 下载 ShareGPT 数据（hf-mirror）：
python -c "
import os
os.environ['HF_ENDPOINT']='https://hf-mirror.com'
from huggingface_hub import hf_hub_download
p = hf_hub_download('anon8231489123/ShareGPT_Vicuna_unfiltered', 'ShareGPT_V3_unfiltered_cleaned_split.json', repo_type='dataset')
print('OK:', p)
"
# 2. 转成 Alpaca parquet：
python exp/make_dataset.py --input <上面输出的路径> --output /root/autodl-tmp/dataset.parquet

# 3. 跑相变：
export VQA_DATA_PATH=/root/autodl-tmp/dataset.parquet
python exp/run_vqa_validation.py --model-path /root/autodl-tmp/llava-hf
```

### 实验 4：Qwen 迁移（~1h）

**推荐：完整版 fp16 权重**（A800 80GB 无压力，绕开 GPTQ/auto-gptq 版本地狱；脚本已自动兼容两种模型）：
```bash
# 1. 下载 Qwen2-VL-7B-Instruct 完整版（ModelScope，国内快，~15GB）：
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2-VL-7B-Instruct', local_dir='/root/qwen2vl_fp16')"

# 2. 跑 Γ + 分配（run_qwen_transfer.py 已改：无 quantize_config.json 时 float16 直载）：
python exp/run_qwen_transfer.py --model-path /root/qwen2vl_fp16

# 3. counterfactual（theory r=4 / violation r=16,32），每个 rank 3 seeds（42/123/456）：
#    run_training_qwen.py 已加 --model-path；bitsandbytes 4bit 加载本地权重（与论文 QLoRA 声明一致）
python scripts/run_training_qwen.py --rank 4 --epochs 3 --seed 42 --model-path /root/qwen2vl_fp16
python scripts/run_training_qwen.py --rank 16 --epochs 3 --seed 42 --model-path /root/qwen2vl_fp16
python scripts/run_training_qwen.py --rank 32 --epochs 3 --seed 42 --model-path /root/qwen2vl_fp16
# （123/456 同理替换 --seed）
```

### 实验 5：OpenCLIP/BitFit（回本地跑）

```bash
# 本地（conda activate pytorch）：
cd D:\Realdesktop\Wan\Important\New
pip install open_clip_torch
python exp/run_openclip_bitfit.py --method openclip
python exp/run_openclip_bitfit.py --method bitfit
```

## 回传

```bash
zip 结果.zip gamma_llava_results.json ers_1epoch_results.json vqa_phase_results.json qwen_transfer_results.json qwen_cf_rank*.json openclip_results.json bitfit_results.json
# 发我 → 我重写论文
```

**实验 4 经验**（2026-08-05）：① 用完整版 fp16 模型（ModelScope 直下，绕开 GPTQ 生态：auto-gptq 镜像 metadata bug + 源码编译失败）；② 32GB 卡跑 4bit bnb（`BitsAndBytesConfig` + gradient_checkpointing），fp16 完整载入会 OOM；③ Γ 点积必须 `.float()` 计算（fp16 点积累加溢出 → vis=-inf）；④ Qwen 架构属性名与 LLaVA 不同（merger 在 `visual` 内、LLM 无固定路径）→ 用动态定位（`named_modules()` 找 'merger'/最大 layers）

---

## 二轮补充实验（2026-08-05，P0：vis Γ 验证 + 块级分配）

### ① vis Γ 量级验证（~30min，先跑）

**目的**：确认 vis=-3.7e8 是真实特性还是 fp32 精度伪影（4bit 反传 fp16 梯度）。结果决定论文 Finding 4 数值是否更新。

```bash
cd /root/autodl-tmp/work
python - <<'EOF'
"""Qwen Γ 量级验证：fp32 compute_dtype 重测"""
import torch, json
from transformers import Qwen2VLForConditionalGeneration, BitsAndBytesConfig, AutoProcessor

quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float32, bnb_4bit_use_double_quant=True)
model = Qwen2VLForConditionalGeneration.from_pretrained('/root/qwen2vl_fp16', quantization_config=quant, device_map="auto")
processor = AutoProcessor.from_pretrained('/root/qwen2vl_fp16')

blank = torch.zeros(1, 3, 336, 336)
text = [processor.apply_chat_template(
    [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": "What is shown?"}]}],
    tokenize=False, add_generation_prompt=True)]
inputs = processor(text=text, images=blank, return_tensors="pt")
input_ids = inputs['input_ids'].to(model.device)
pixel_values = inputs['pixel_values'].to(model.device, dtype=torch.float32)
image_grid_thw = inputs['image_grid_thw'].to(model.device)

outputs = model(input_ids=input_ids, pixel_values=pixel_values, image_grid_thw=image_grid_thw, output_hidden_states=True)
hidden = outputs.hidden_states[-1]
pad_id = processor.tokenizer.convert_tokens_to_ids("<|image_pad|>")
vis_mask = (input_ids == pad_id)
lang_mask = (input_ids != pad_id) & (input_ids != processor.tokenizer.pad_token_id)
E = torch.mean(torch.sum((hidden[vis_mask].mean(0) - hidden[lang_mask].mean(0)) ** 2))
E.backward(retain_graph=True)
grad_E = {p: p.grad.detach().clone() for n, p in model.named_parameters() if p.requires_grad and p.grad is not None}
model.zero_grad()
loss = model(input_ids=input_ids, pixel_values=pixel_values, image_grid_thw=image_grid_thw, labels=input_ids).loss
loss.backward()
grad_u = {p: p.grad.detach().clone() for n, p in model.named_parameters() if p.requires_grad and p.grad is not None}

groups = {}
vis = [p for n, p in model.visual.named_parameters() if p.requires_grad]
if vis: groups['vis'] = vis
merger = []
for n_, m_ in model.named_modules():
    if 'merger' in n_.lower(): merger += [p for p in m_.parameters() if p.requires_grad]
if merger: groups['merger'] = merger
llm, best = None, 0
for n_, m_ in model.named_modules():
    if hasattr(m_, 'layers') and isinstance(m_.layers, torch.nn.ModuleList) and len(m_.layers) > best:
        llm, best = m_, len(m_.layers)
for i, layer in enumerate(llm.layers):
    target = 'llm_shallow' if i <= best // 4 else 'llm_mid' if i <= 3 * best // 4 else 'llm_deep'
    groups.setdefault(target, []).extend(p for n, p in layer.named_parameters() if p.requires_grad)

print('\n=== fp32 重测 Gamma ===')
for block, params in groups.items():
    if not params: continue
    gE = torch.cat([grad_E[p].flatten() for p in params if p in grad_E]).float()
    u  = torch.cat([grad_u[p].flatten() for p in params if p in grad_u]).float()
    g = float(torch.dot(gE, u))
    nE = float(torch.norm(gE)); nu = float(torch.norm(u))
    print('%-12s Gamma=%-14.4e  |gE|=%-10.3e |u|=%-10.3e cos=%.3f' % (block, g, nE, nu, g/(nE*nu) if nE*nu > 0 else 0))
print('\n对比 fp16: vis=-3.74e8, merger=-2.10e4, shallow=-8.97e2, mid=-2.06e3, deep=-7.21e3')
EOF
```

**判断**：vis 仍 ~1e7-1e8 → 真实特性（论文表述成立）；回落 ~1e5-1e6 → fp16 伪影（论文数值需更新，结果发我）。

=== fp32 重测 Gamma ===
vis          Gamma=-3.7520e+08     |gE|=2.749e+06  |u|=5.216e+02  cos=-0.262
merger       Gamma=-2.1090e+04     |gE|=1.591e+04  |u|=3.934e+00  cos=-0.337
llm_shallow  Gamma=-8.9689e+02     |gE|=5.644e+03  |u|=5.589e-01  cos=-0.284
llm_mid      Gamma=-2.0754e+03     |gE|=8.827e+03  |u|=1.398e+00  cos=-0.168
llm_deep     Gamma=-7.2314e+03     |gE|=8.455e+03  |u|=1.596e+00  cos=-0.536

对比 fp16: vis=-3.74e8, merger=-2.10e4, shallow=-8.97e2, mid=-2.06e3, deep=-7.21e3

### ② 块级分配补丁（改 run_training_qwen.py，~1min）

```bash
cd /root/autodl-tmp/work
python - <<'EOF'
p = 'scripts/run_training_qwen.py'
src = open(p).read()

# 1. 加 --block-config 参数
old_a = "parser.add_argument('--model-path', type=str, default='/root/qwen2vl_fp16',"
new_a = old_a + "\nparser.add_argument('--block-config', type=str, default='uniform',\n                    choices=['uniform', 'theory', 'violation'],\n                    help='theory: shallow(0-7) r8/其余 r2; violation: deep(20-27) r8/其余 r2; uniform: 全层 r4')"
assert old_a in src, '参数模板未匹配'
src = src.replace(old_a, new_a, 1)

# 2. 替换 LoRA 配置块（rank_pattern 按层不同 rank）
old_l = 'peft_cfg = LoraConfig(r=args.rank, lora_alpha=args.rank*2, target_modules=["q_proj","k_proj","v_proj","o_proj"], lora_dropout=0.1, bias="none", task_type=TaskType.CAUSAL_LM)'
new_l = '''bc = getattr(args, 'block_config', 'uniform')
if bc == 'theory':
    lora_rank, rank_pattern = 2, {r".*layers\\\\.([0-7])\\\\.": 8}
elif bc == 'violation':
    lora_rank, rank_pattern = 2, {r".*layers\\\\.(2[0-7])\\\\.": 8}
else:
    lora_rank, rank_pattern = 4, {}
peft_cfg = LoraConfig(r=lora_rank, lora_alpha=16, rank_pattern=rank_pattern,
                      target_modules=["q_proj","k_proj","v_proj","o_proj"],
                      lora_dropout=0.1, bias="none", task_type=TaskType.CAUSAL_LM)'''
assert old_l in src, 'LoRA 模板未匹配'
src = src.replace(old_l, new_l, 1)

# 3. 保存名带 config 前缀
old_s = 'save_path = os.path.join(os.getcwd(), f"qwen_cf_rank{args.rank}_seed{args.seed}.json")'
new_s = 'bc = getattr(args, "block_config", "uniform")\nsave_path = os.path.join(os.getcwd(), f"qwen_cf_{bc}_rank{args.rank}_seed{args.seed}.json")'
assert old_s in src, '保存名模板未匹配'
src = src.replace(old_s, new_s, 1)

open(p, 'w').write(src)
print('补丁完成（3 处）')
EOF
```

### ③ 跑块级分配（9 runs，~2-3h）

```bash
cd /root/autodl-tmp/work
for cfg in theory violation uniform; do
  for seed in 42 123 456; do
    python scripts/run_training_qwen.py --block-config $cfg --epochs 3 --seed $seed --model-path /root/qwen2vl_fp16
  done
done
```

**配置说明**：uniform=r4 全层（对照，与旧 counterfactual r4 可比）；theory=shallow(0-7) r8/其余 r2（预测最优）；violation=deep(20-27) r8/其余 r2（预测最差）。每 run 存 `qwen_cf_{cfg}_rank4_seed{s}.json`（E 轨迹 + ΔE）。

### ④ 回传

```bash
zip 块级.zip qwen_cf_theory*.json qwen_cf_violation*.json qwen_cf_uniform*.json
# + ① 的 fp32 Γ 输出（直接复制发我）
```

## 结果保存位置（回传后我放这）

| 结果 | 位置 |
|------|------|
| gamma/ers/vqa/qwen | `paper3/scripts/outputs/experiments/` |
| openclip/bitfit | `outputs/theory/openclip/` `outputs/theory/bitfit/` |

## 环境备忘（踩过的坑）

```bash
_fast_init=False        # 跳过 Byte 权重初始化 bug
use_fast=False          # tokenizer 用 SentencePiece（pip install sentencepiece）
processor.patch_size=14 # preprocessor_config.json 手写 + 手动设 patch_size
pixel_values=...        # 4.48 用 pixel_values 不是 images
# 输入全部 .to(model.device)
# compute_gamma_llava.py 已修：grad key tensor→name、images→pixel_values
# 模型必须 llava-hf（liuhaotian 原版 image_token_index 越界）
```