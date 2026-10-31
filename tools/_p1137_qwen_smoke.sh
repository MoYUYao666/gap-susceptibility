#!/usr/bin/env bash
# Qwen2.5-VL-7B smoke test: does it fit, does it train, does the canonical metric compute, is the checkpoint real?
#
# Context. On 2026-10-16 the same model was judged not to fit in 32 GB:
#     OutOfMemoryError ... 31.09 GiB allocated of 31.48 GiB usable
# but that run's measurement path used `output_hidden_states=True`, and the same flag was later measured to
# allocate 29.81 GiB on LLaVA -- far more than the tensor it promises, and it was replaced with an `lm_head`
# forward pre-hook. So the earlier conclusion may have been an artefact of the measurement, not the model, and it
# is being re-tested here with the corrected runner.
#
# Every step reports, so a failure is diagnosable rather than just an OOM line:
#   1. load the weights in bf16 (no quantisation) and report peak memory;
#   2. three training steps on 16 pairs, reporting s/step;
#   3. measure the canonical DG*/CG on the held-out pairs;
#   4. confirm the checkpoint's `model` dict is non-empty.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_eval
MODEL=/root/autodl-tmp/hf/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/main

pkill -9 -f _p1135_qwen_sites || true
for i in $(seq 1 40); do
  u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$u" -lt 2000 ] && break; sleep 5
done

echo "=== model present? ==="
ls -la "$MODEL" | head -14
df -h /root/autodl-tmp | tail -1

echo
echo "=== imports ==="
$PY -c "
import importlib
for m in ('torch','transformers','peft','accelerate'):
    try: print('  %-14s %s' % (m, importlib.import_module(m).__version__))
    except Exception as e: print('  %-14s MISSING %s' % (m, type(e).__name__))
from transformers import Qwen2_5_VLForConditionalGeneration as Q
print('  Qwen2_5_VLForConditionalGeneration available:', Q is not None)
"

echo
echo "=== smoke: 3 steps, 16 pairs, eval-batch 4, max-len 1024 ==="
rm -rf outputs/smoke_qwen
$PY -u -X utf8 tools/_p1135_qwen_sites.py \
  --coco-root "$COCO" --model "$MODEL" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 16 --eval-pairs 8 --epochs 1 --batch 2 --eval-batch 4 --max-len 1024 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 3 --report-every 1 --apply \
  --out-dir outputs/smoke_qwen > /root/p3/smoke_qwen.out 2>&1
echo "  exit=$?"
echo
echo "=== key output ==="
grep -aE "model_type|load|parameters|trainable|batch tokens|sequence length|canonical DG|legacy|ARM FAILED|Traceback|Error|OutOfMemory" \
  /root/p3/smoke_qwen.out | head -18
echo
echo "=== last lines if it failed ==="
tail -14 /root/p3/smoke_qwen.out
echo
echo "=== peak memory during the run ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
echo
echo "=== checkpoint non-empty? ==="
$PY - <<'PYEOF'
import glob, torch
from pathlib import Path
fs = sorted(glob.glob("/root/p3/outputs/smoke_qwen/*.pt"))
if not fs:
    print("  NO CHECKPOINT")
else:
    for f in fs:
        o = torch.load(f, map_location="cpu")
        m = o.get("model", {}) or {}
        print(f"  {Path(f).name}: {Path(f).stat().st_size/1e6:.1f} MB | model tensors: {len(m)}")
        for k in list(m)[:3]:
            print(f"      {k} {tuple(m[k].shape)}")
PYEOF
echo QWEN_SMOKE_DONE
