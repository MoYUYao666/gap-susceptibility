#!/usr/bin/env bash
# Smoke-test bf16 on the 24 GB device with the allocator warm-up capped, then run the full sweep if it fits.
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

pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 30); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting for the device: ${used} MiB"; sleep 10
done

echo "=== smoke: bf16 with the warm-up capped at 1.5 GB ==="
rm -rf outputs/smoke_4090
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/smoke_4090 2>&1 | grep -Ev "Loading weights|it/s\]" | tail -14
echo "  memory after the smoke run:"; nvidia-smi --query-gpu=memory.used --format=csv,noheader
if ! grep -q "bench stop after 5 steps" outputs/smoke_4090/../smoke_4090/*.json 2>/dev/null && \
   ! ls outputs/smoke_4090/*.json >/dev/null 2>&1; then
  echo "SMOKE_FAILED -- not starting the sweep"; exit 1
fi

echo "=== full sweep: bf16, 1500 train / 500 held out, 3 epochs, 3 seeds, 4 arms ==="
rm -rf outputs/llava_bf16_sites
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites 2>&1 | grep -Ev "Loading weights|it/s\]"
echo BF16_SWEEP_DONE
