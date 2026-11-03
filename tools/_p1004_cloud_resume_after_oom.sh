#!/usr/bin/env bash
# Restart the sweep after the OOM at the second model load, with the allocator warm-up capped.
#
# What happened at 10:18: `text_only_s42` finished, then loading the next model died with
#   torch.OutOfMemoryError: Tried to allocate 13.03 GiB ... 4.29 GiB free
# The 13.03 GiB is the warm-up reservation transformers makes before loading, which is a copy of the model's
# own size. It is not needed here and it is what fails when a previous run's allocation has not been fully
# released. `--alloc-warmup-gb 1.5` caps it.
#
# Restarting keeps every finished record: `frozen_s42/s123/s456` and `text_only_s42` are read from
# outputs/llava_bf16_sites and skipped, so nothing already measured is repeated or lost.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

echo "=== device before ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

echo "=== existing records (these will be skipped) ==="
ls outputs/llava_bf16_sites/*.json 2>/dev/null | xargs -n1 basename

echo "=== free the device, and prove it went back to zero ==="
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 40); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting: ${used} MiB"; sleep 10
done
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

echo "=== resume: bf16, 1500 train / 500 held out, batch 2, eval-batch 32, 3 epochs, 3 seeds, 4 arms ==="
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --eval-batch 32 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites 2>&1 | grep -Ev "Loading weights|it/s\]"
echo BF16_SWEEP_DONE
