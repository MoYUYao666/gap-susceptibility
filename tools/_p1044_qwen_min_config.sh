#!/usr/bin/env bash
# Smallest configuration that could fit Qwen2.5-VL on this device, with step timing.
#
# The previous attempt showed the limit is the model plus its optimiser, not activations:
#   31.46 GiB in use, 1.69 MiB free, failing on a 30 MiB allocation
# and switching gradient checkpointing off did not change that peak. Qwen2.5-VL holds
# 8,292,166,656 parameters (16.6 GB in bf16) against LLaVA's 7.06 B, so it needs about 2.6 GB more before any
# activation. This run therefore pushes everything else to its minimum -- batch 1, max-len 512, eval-batch 1 --
# and reports the step time, because that number decides whether a full sweep is even arithmetic-feasible.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

pkill -9 -f _p1035_qwen_sites || true
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 60); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting for the device: ${used} MiB"; sleep 10
done

echo "=== A: batch 1, max-len 512, eval-batch 1, gradient checkpointing ON, 10 steps ==="
rm -rf outputs/qwen_min
$PY -u -X utf8 tools/_p1035_qwen_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 10 --eval-pairs 4 --epochs 1 --batch 1 --eval-batch 1 --max-len 512 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 10 --report-every 5 --apply \
  --out-dir outputs/qwen_min > /root/p3/qwen_min.out 2>&1
echo "  exit=$?"
grep -aE "batch tokens|sequence length|step [0-9]+/|epoch 1/1|held-out|DG\*|measurement failed|OutOfMemory" \
  /root/p3/qwen_min.out | head -12
echo "  peak: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader)"

echo
echo "=== B: same but max-len 1024 (only if A fit) ==="
if grep -aq "epoch 1/1" /root/p3/qwen_min.out; then
  pkill -9 -f _p1035_qwen_sites || true
  sleep 15
  rm -rf outputs/qwen_min2
  $PY -u -X utf8 tools/_p1035_qwen_sites.py \
    --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 \
    --samples 10 --eval-pairs 4 --epochs 1 --batch 1 --eval-batch 1 --max-len 1024 \
    --seeds 1 --rank 8 --arms text_only --bench-steps 10 --report-every 5 --apply \
    --out-dir outputs/qwen_min2 > /root/p3/qwen_min2.out 2>&1
  echo "  exit=$?"
  grep -aE "batch tokens|sequence length|step [0-9]+/|epoch 1/1|held-out|measurement failed|OutOfMemory" \
    /root/p3/qwen_min2.out | head -12
fi
echo QWEN_MIN_DONE
