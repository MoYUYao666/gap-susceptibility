#!/usr/bin/env bash
# Kill anything left holding the GPU, wait for the memory to actually come back, then start the sweep.
#
# Learned here: `pkill -f _p820_llava_sites` did not free the device -- the old process was still holding
# 29.24 GiB when the next run tried to load, so the load died with CUDA out of memory while the GPU looked
# busy. The kill is now verified by polling nvidia-smi rather than assumed.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

echo "=== clearing the device ==="
pkill -9 -f _p820_llava_sites || true
pkill -9 -f _p981_cloud_bf16_sweep || true
for i in $(seq 1 30); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  echo "  wait $i: ${used} MiB in use"
  [ "$used" -lt 2000 ] && break
  sleep 10
done
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
pgrep -af '_p820_llava_sites' | head -3 || echo "  no sweep process running"

echo "=== annotations ==="
ls -la "$COCO/annotations/"
[ -f "$COCO/annotations/captions_val2014.json" ] || cp -f "$COCO/annotations/captions_run.json" "$COCO/annotations/captions_val2014.json"

echo "=== sweep: bf16, 1500 train / 500 held out, 3 epochs, 3 seeds, 4 arms ==="
rm -rf outputs/llava_bf16_sites
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites 2>&1 | grep -Ev "Loading weights|it/s\]"
echo BF16_SWEEP_DONE
