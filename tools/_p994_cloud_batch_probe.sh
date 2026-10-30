#!/usr/bin/env bash
# Find the largest training batch that fits, and how much faster it is, WITHOUT changing the experiment.
#
# The sweep is step-bound: 2250 steps per run at batch 2, because 1500 training pairs / 2 = 750 per epoch.
# Raising the batch keeps every sample, every epoch and every seed identical -- only the number of samples
# per optimisation step changes, which is the standard throughput knob. This measures batch 4 and 8 over
# 30 steps each, with the pair count and sequence length fixed, and records the peak memory so the choice
# is made on numbers rather than on hope.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

echo "=== stopping the current run (it is restarted afterwards with the chosen batch) ==="
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 30); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting: ${used} MiB"; sleep 10
done

for B in 2 4 8; do
  echo
  echo "=== batch $B, 30 steps, 1500-sample workload ==="
  rm -rf outputs/batchprobe
  START=$(date +%s)
  $PY -u -X utf8 tools/_p820_llava_sites.py \
    --coco-root "$COCO" --precision bf16 \
    --samples 1500 --eval-pairs 20 --epochs 1 --batch "$B" --eval-batch 32 \
    --max-len 2048 --seeds 1 --rank 8 --arms text_only \
    --bench-steps 30 --report-every 10 --apply \
    --out-dir outputs/batchprobe 2>&1 | grep -E "batch tokens|s/step|bench stop|peak|measurement" | tail -6
  END=$(date +%s)
  echo "  wall: $((END-START)) s | memory now: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader)"
  if grep -q "CUDA out of memory" outputs/batchprobe/../batchprobe/*.json 2>/dev/null; then echo "  OOM"; fi
done
echo
echo "=== done: pick the largest batch that stayed comfortably inside the device ==="
echo BATCHPROBE_DONE
