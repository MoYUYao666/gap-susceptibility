#!/usr/bin/env bash
# Measure two speed options that do not change what is computed:
#   1. batch 4 instead of 2 (same samples, same epochs, same seeds -- just more per step);
#   2. the same with TF32 enabled, which the script never sets. On the RTX 40 series TF32 is the normal
#      path for fp32 matmuls in a bf16 training loop; without it those matmuls run in full fp32, which is
#      slower and buys nothing here. Measured the same way, so the gain is a number rather than a guess.
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

run() {  # $1 label, $2 batch, $3 extra python bootstrap
  echo
  echo "=== $1 ==="
  rm -rf outputs/probe2
  if [ -n "$3" ]; then export PYTHONSTARTUP=""; fi
  $PY -u -X utf8 ${3:+-c "$3" } tools/_p820_llava_sites.py \
    --coco-root "$COCO" --precision bf16 \
    --samples 1500 --eval-pairs 20 --epochs 1 --batch "$2" --eval-batch 32 \
    --max-len 2048 --seeds 1 --rank 8 --arms text_only \
    --bench-steps 25 --report-every 25 --apply \
    --out-dir outputs/probe2 2>&1 | grep -E "s/step|measurement" | tail -3
}

run "batch 2, TF32 as the script leaves it (off)" 2 ""
run "batch 4, TF32 off" 4 ""
run "batch 4, TF32 on" 4 "import torch;torch.backends.cuda.matmul.allow_tf32=True;torch.backends.cudnn.allow_tf32=True;exec(open('tools/_p820_llava_sites.py').read())"
echo
echo TF32_PROBE_DONE
