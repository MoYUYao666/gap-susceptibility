#!/usr/bin/env bash
# Compare three settings on the same 25 steps, to pick the fastest one that changes nothing about the
# experiment: batch 2 (the original), batch 4, and batch 4 with TF32 allowed for fp32 matmuls.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 30); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  sleep 10
done

probe() {  # label, extra args...
  local label="$1"; shift
  echo
  echo "=== $label ==="
  rm -rf outputs/probe3
  $PY -u -X utf8 tools/_p820_llava_sites.py \
    --coco-root "$COCO" --precision bf16 \
    --samples 1500 --eval-pairs 100 --epochs 1 --eval-batch 50 \
    --max-len 2048 --seeds 1 --rank 8 --arms text_only \
    --bench-steps 25 --report-every 25 --apply --out-dir outputs/probe3 "$@" 2>&1 \
    | grep -E "s/step|measurement|TF32" | tail -4
}

probe "batch 2, no TF32 (the configuration that is running now)" --batch 2
probe "batch 4, no TF32" --batch 4
probe "batch 4, TF32 on" --batch 4 --tf32
probe "batch 2, TF32 on" --batch 2 --tf32
echo
echo TF32_PROBE_DONE
