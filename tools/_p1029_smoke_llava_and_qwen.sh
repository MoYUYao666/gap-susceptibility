#!/usr/bin/env bash
# Two smoke runs: prove the refactor did not change LLaVA's numbers, then prove Qwen loads and trains.
#
# The prompt path and the image-token detection were generalised for Qwen, which touches code the LLaVA
# results came from, so the first check is a five-step LLaVA run whose loss must match the frozen baseline
# (2.9466 for the deterministic 5-step parity run of 2026-10-15). If that holds, the refactor is
# behaviour-preserving and the second check can look at Qwen.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_OFFLINE=0
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 40); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting for the device: ${used} MiB"; sleep 10
done

echo "############ 1. LLaVA regression check (must match the 2.9466 baseline) ############"
rm -rf outputs/smoke_llava_refactor
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 --deterministic \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/smoke_llava_refactor 2>&1 | grep -E "loss |batch tokens|step " | head -8

echo
echo "############ 2. Qwen/Qwen2.5-VL-7B-Instruct smoke ############"
rm -rf outputs/smoke_qwen
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --model Qwen/Qwen2.5-VL-7B-Instruct --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/smoke_qwen 2>&1 | tail -30
echo
echo "=== device after both smokes ==="
nvidia-smi --query-gpu=memory.used --format=csv,noheader
echo SMOKES_DONE
