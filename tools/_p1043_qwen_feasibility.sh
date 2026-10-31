#!/usr/bin/env bash
# Measure Qwen2.5-VL's step time and peak memory before committing to a sweep.
#
# The measurement pass is what ran out of memory (31.46 GiB in use, 5.69 MiB free), because Qwen2.5-VL's
# dynamic resolution gives longer sequences than LLaVA's and the first version kept all 29 hidden states.
# This run removes that cost and measures what remains:
#   * hooks instead of output_hidden_states  (one tensor instead of 29 per batch)
#   * --eval-batch 4  instead of 32
#   * --max-len 1024  (Qwen's own prompts measured 418 tokens for one image, so 1024 has room)
#   * gradient checkpointing OFF, which trades memory for time; if it does not fit, the log says so
# Reports s/step and peak memory, so the full-sweep estimate is arithmetic rather than a guess.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
COCO=/root/p3/coco_full

pkill -9 -f _p1035_qwen_sites || true
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 60); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting for the device: ${used} MiB"; sleep 10
done

echo "=== Qwen, hooks + eval-batch 4 + max-len 1024, 15 steps ==="
rm -rf outputs/qwen_probe
$PY -u -X utf8 tools/_p1035_qwen_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 --no-grad-ckpt \
  --samples 20 --eval-pairs 8 --epochs 1 --batch 2 --eval-batch 4 --max-len 1024 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 15 --report-every 5 --apply \
  --out-dir outputs/qwen_probe > /root/p3/qwen_probe.out 2>&1
echo "exit=$?"
echo
echo "=== results ==="
grep -aE "batch tokens|sequence length|trainable|step [0-9]+/|epoch 1/1|held-out|DG\*|OOM|OutOfMemory|Error" \
  /root/p3/qwen_probe.out | head -18
echo
echo "=== peak memory during the run ==="
nvidia-smi --query-gpu=memory.used --format=csv,noheader
echo QWEN_PROBE_DONE
