# Supplementary experiments — command-line cheat sheet

## 🔴 Model acquisition rules (explicit user requirement)

**All models must be downloaded directly on the server (ModelScope / HF mirror); "download locally → upload to server" is forbidden.**

```bash
# ModelScope (recommended):
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2-VL-7B-Instruct', local_dir='/root/qwen2vl_fp16')"

# HF mirror (fallback):
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
```

## Main line

**Model**: llava-hf (required; only vocab=32064 allows image_token_index=32000)
**Scripts**: all of exp/ is ready (including make_dataset.py for dataset conversion)

## Progress

- [x] Experiment 1 (Γ) ✅ written into Paper 3 appendix (mid-dominant 41.2%, vis negative coupling)
- [x] Experiment 2 (ERS 1-epoch) ✅ written into Paper 3 (r64 flips +151.7, no plateau, reported honestly)
- [x] Experiment 3 (ShareGPT) ✅ written into Paper 3 (r_c∈[5,6] reproduced on two datasets)
- [x] Experiment 4 (Qwen) ✅ done (2026-08-05) — full fp16 + 4bit bnb loading; Γ all negative; counterfactual rank insensitive (p=0.95) → written into Paper 3 Finding 4 (C4 verification)
- [x] Experiment 5a (OpenCLIP) ✅ written into Paper A (R²=0.943, α=-0.002, β=0.484)
- [x] Experiment 5b (BitFit) ✅ written into Paper A (β≈0 boundary case)

## Experiment commands

### Experiment 1: Γ measurement (multiple ranks, multiple batches, ~30min)

```bash
cd /root/autodl-tmp/work
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
python exp/run_gamma_llava.py --ranks 4,8,16,32,64 --batches 5 --model-path /root/autodl-tmp/llava-hf
```

### Experiment 2: ERS 1-epoch (4 ranks × 3 seeds, ~1h)

```bash
python exp/run_ers_1epoch.py --model-path /root/autodl-tmp/llava-hf
```

### Experiment 3: second-dataset phase transition (~4h)

```bash
# 1. Download the ShareGPT data (hf-mirror):
python -c "
import os
os.environ['HF_ENDPOINT']='https://hf-mirror.com'
from huggingface_hub import hf_hub_download
p = hf_hub_download('anon8231489123/ShareGPT_Vicuna_unfiltered', 'ShareGPT_V3_unfiltered_cleaned_split.json', repo_type='dataset')
print('OK:', p)
"
# 2. Convert to Alpaca parquet:
python exp/make_dataset.py --input <path printed above> --output /root/autodl-tmp/dataset.parquet

# 3. Run the phase transition:
export VQA_DATA_PATH=/root/autodl-tmp/dataset.parquet
python exp/run_vqa_validation.py --model-path /root/autodl-tmp/llava-hf
```

### Experiment 4: Qwen transfer (~1h)

**Recommended: full fp16 weights** (A800 80GB handles it easily, avoiding GPTQ/auto-gptq version hell; the script already supports both models automatically):
```bash
# 1. Download the full Qwen2-VL-7B-Instruct (ModelScope, fast domestically, ~15GB):
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2-VL-7B-Instruct', local_dir='/root/qwen2vl_fp16')"

# 2. Run Γ + allocation (run_qwen_transfer.py already changed: loads float16 directly when there is no quantize_config.json):
python exp/run_qwen_transfer.py --model-path /root/qwen2vl_fp16

# 3. counterfactual (theory r=4 / violation r=16,32), 3 seeds per rank (42/123/456):
#    run_training_qwen.py now has --model-path; bitsandbytes 4bit loads local weights (consistent with the paper's QLoRA statement)
python scripts/run_training_qwen.py --rank 4 --epochs 3 --seed 42 --model-path /root/qwen2vl_fp16
python scripts/run_training_qwen.py --rank 16 --epochs 3 --seed 42 --model-path /root/qwen2vl_fp16
python scripts/run_training_qwen.py --rank 32 --epochs 3 --seed 42 --model-path /root/qwen2vl_fp16
# (same for 123/456, just replace --seed)
```

### Experiment 5: OpenCLIP/BitFit (run locally)

```bash
# locally (conda activate pytorch):
cd D:\Realdesktop\Wan\Important\New
pip install open_clip_torch
python exp/run_openclip_bitfit.py --method openclip
python exp/run_openclip_bitfit.py --method bitfit
```

## Sending results back

```bash
zip 结果.zip gamma_llava_results.json ers_1epoch_results.json vqa_phase_results.json qwen_transfer_results.json qwen_cf_rank*.json openclip_results.json bitfit_results.json
# send to me → I rewrite the paper
```

**Experiment 4 lessons** (2026-08-05): ① use the full fp16 model (downloaded straight from ModelScope, avoiding the GPTQ ecosystem: auto-gptq mirror metadata bug + source build failure); ② a 32GB card runs 4bit bnb (`BitsAndBytesConfig` + gradient_checkpointing); loading the full fp16 will OOM; ③ Γ dot products must be computed in `.float()` (fp16 dot-product accumulation overflows → vis=-inf); ④ Qwen's architecture attribute names differ from LLaVA (merger is inside `visual`, the LLM has no fixed path) → use dynamic location (search `named_modules()` for 'merger'/the largest layers)

---

## Second round of supplementary experiments (2026-08-05, P0: vis Γ verification + block-level allocation)

### ① vis Γ magnitude verification (~30min, run first)

**Purpose**: confirm whether vis=-3.7e8 is a real property or an fp32 precision artefact (fp16 gradients from 4bit backprop). The result decides whether Paper Finding 4's numbers are updated.

```bash
cd /root/autodl-tmp/work
python - <<'EOF'
"""Qwen Γ magnitude verification: re-measure with fp32 compute_dtype"""
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

print('\n=== fp32 re-measured Gamma ===')
for block, params in groups.items():
    if not params: continue
    gE = torch.cat([grad_E[p].flatten() for p in params if p in grad_E]).float()
    u  = torch.cat([grad_u[p].flatten() for p in params if p in grad_u]).float()
    g = float(torch.dot(gE, u))
    nE = float(torch.norm(gE)); nu = float(torch.norm(u))
    print('%-12s Gamma=%-14.4e  |gE|=%-10.3e |u|=%-10.3e cos=%.3f' % (block, g, nE, nu, g/(nE*nu) if nE*nu > 0 else 0))
print('\ncompare with fp16: vis=-3.74e8, merger=-2.10e4, shallow=-8.97e2, mid=-2.06e3, deep=-7.21e3')
EOF
```

**Verdict**: vis still ~1e7-1e8 → real property (the paper's statement holds); falls back to ~1e5-1e6 → fp16 artefact (the paper's numbers need updating, send me the result).

=== fp32 re-measured Gamma ===
vis          Gamma=-3.7520e+08     |gE|=2.749e+06  |u|=5.216e+02  cos=-0.262
merger       Gamma=-2.1090e+04     |gE|=1.591e+04  |u|=3.934e+00  cos=-0.337
llm_shallow  Gamma=-8.9689e+02     |gE|=5.644e+03  |u|=5.589e-01  cos=-0.284
llm_mid      Gamma=-2.0754e+03     |gE|=8.827e+03  |u|=1.398e+00  cos=-0.168
llm_deep     Gamma=-7.2314e+03     |gE|=8.455e+03  |u|=1.596e+00  cos=-0.536

compare with fp16: vis=-3.74e8, merger=-2.10e4, shallow=-8.97e2, mid=-2.06e3, deep=-7.21e3

### ② Block-level allocation patch (edit run_training_qwen.py, ~1min)

```bash
cd /root/autodl-tmp/work
python - <<'EOF'
p = 'scripts/run_training_qwen.py'
src = open(p).read()

# 1. Add the --block-config argument
old_a = "parser.add_argument('--model-path', type=str, default='/root/qwen2vl_fp16',"
new_a = old_a + "\nparser.add_argument('--block-config', type=str, default='uniform',\n                    choices=['uniform', 'theory', 'violation'],\n                    help='theory: shallow(0-7) r8/rest r2; violation: deep(20-27) r8/rest r2; uniform: all layers r4')"
assert old_a in src, 'argument template did not match'
src = src.replace(old_a, new_a, 1)

# 2. Replace the LoRA config block (rank_pattern gives per-layer ranks)
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
assert old_l in src, 'LoRA template did not match'
src = src.replace(old_l, new_l, 1)

# 3. Save name carries the config prefix
old_s = 'save_path = os.path.join(os.getcwd(), f"qwen_cf_rank{args.rank}_seed{args.seed}.json")'
new_s = 'bc = getattr(args, "block_config", "uniform")\nsave_path = os.path.join(os.getcwd(), f"qwen_cf_{bc}_rank{args.rank}_seed{args.seed}.json")'
assert old_s in src, 'save-name template did not match'
src = src.replace(old_s, new_s, 1)

open(p, 'w').write(src)
print('patch done (3 places)')
EOF
```

### ③ Run block-level allocation (9 runs, ~2-3h)

```bash
cd /root/autodl-tmp/work
for cfg in theory violation uniform; do
  for seed in 42 123 456; do
    python scripts/run_training_qwen.py --block-config $cfg --epochs 3 --seed $seed --model-path /root/qwen2vl_fp16
  done
done
```

**Config notes**: uniform=r4 on all layers (control, comparable to the old counterfactual r4); theory=shallow(0-7) r8 / rest r2 (predicted best); violation=deep(20-27) r8 / rest r2 (predicted worst). Each run saves `qwen_cf_{cfg}_rank4_seed{s}.json` (E trajectory + ΔE).

### ④ Sending back

```bash
zip 块级.zip qwen_cf_theory*.json qwen_cf_violation*.json qwen_cf_uniform*.json
# + the fp32 Γ output from ① (just copy and send to me)
```

## Where results are stored (I put them here after you send them back)

| Result | Location |
|------|------|
| gamma/ers/vqa/qwen | `paper3/scripts/outputs/experiments/` |
| openclip/bitfit | `outputs/theory/openclip/` `outputs/theory/bitfit/` |

## Environment notes (pitfalls hit before)

```bash
_fast_init=False        # skips the Byte weight-init bug
use_fast=False          # tokenizer uses SentencePiece (pip install sentencepiece)
processor.patch_size=14 # preprocessor_config.json written by hand + set patch_size manually
pixel_values=...        # 4.48 uses pixel_values, not images
# cast all inputs with .to(model.device)
# compute_gamma_llava.py already fixed: grad key tensor→name, images→pixel_values
# the model must be llava-hf (the original liuhaotian has an out-of-range image_token_index)
```