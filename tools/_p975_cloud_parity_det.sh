#!/usr/bin/env bash
# Hard parity test: the same run as the local machine's --deterministic baseline.
# If the two agree step for step, the cloud port is proven correct and any speed difference is hardware.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python

rm -rf outputs/llava_parity_clouddet
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root cloud_fixture \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 \
  --deterministic --apply \
  --out-dir outputs/llava_parity_clouddet 2>&1 | grep -Ev "Loading weights|it/s\]" | tail -25
echo CLOUD_DET_DONE
