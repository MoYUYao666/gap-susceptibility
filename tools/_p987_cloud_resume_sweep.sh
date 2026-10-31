#!/usr/bin/env bash
# Smoke first, then the full bf16 sweep, on the restarted host (RTX 4090 D, 24 GB).
#
# The environment and the data survived the restart, so nothing is reinstalled. The device is smaller than
# the first host's (24 GB against 32.8 GB), and the earlier bf16 run used 29.95 GB, so a five-step smoke
# run comes first: if bf16 does not fit here, the sweep must fall back to 4-bit or a smaller max-len rather
# than dying two hours in.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

echo "=== device ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

echo "=== clear the device and wait until the memory is really back ==="
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 30); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  echo "  wait $i: ${used} MiB"
  [ "$used" -lt 2000 ] && break
  sleep 10
done

echo "=== fixture ==="
ls "$COCO/val2014" | wc -l
[ -f "$COCO/annotations/captions_val2014.json" ] || cp "$COCO/annotations/captions_run.json" "$COCO/annotations/captions_val2014.json"

echo "=== smoke: bf16, 5 steps, records the peak memory ==="
rm -rf outputs/smoke_4090
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/smoke_4090 2>&1 | grep -Ev "Loading weights|it/s\]" | tail -12
echo "  peak memory after the smoke run:"
nvidia-smi --query-gpu=memory.used --format=csv,noheader

echo "=== full sweep: bf16, 1500 train / 500 held out, 3 epochs, 3 seeds, 4 arms ==="
rm -rf outputs/llava_bf16_sites
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites 2>&1 | grep -Ev "Loading weights|it/s\]"
echo BF16_SWEEP_DONE
