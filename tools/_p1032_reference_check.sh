#!/usr/bin/env bash
# Prove the restored sweep reproduces the reference loss before anything else is attempted.
#
# The reference is the frozen local record outputs/llava_parity_local/text_only_s42.json: samples 20, epochs 1,
# batch 2, n_eval 10, seed 42, text_only, deterministic, rank 8 -- five steps, loss 2.9496 (the deterministic
# run; 2.9466 and 2.9449 are the non-deterministic repeats). A patched version gave 4.3099 for this exact
# configuration, which is how the prompt refactor was caught.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export PYTORCH_ALLOC_PROC=expandable_segments:True
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 40); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting for the device: ${used} MiB"; sleep 10
done

echo "=== which sweep is on the host ==="
grep -c "apply_chat_template" tools/_p820_llava_sites.py
grep -c "arm_guard" tools/_p820_llava_sites.py

echo "=== reference check: five deterministic steps, expected loss about 2.9496 ==="
rm -rf outputs/refcheck
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 --deterministic --alloc-warmup-gb 1.5 \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/refcheck 2>&1 | grep -E "batch tokens|epoch 1/1|step 5/|loss" | head -6
echo REFCHECK_DONE
