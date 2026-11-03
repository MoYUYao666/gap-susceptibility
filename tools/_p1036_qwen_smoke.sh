#!/usr/bin/env bash
# Smoke-test the Qwen2.5-VL runner before committing to a full sweep.
#
# What this checks, in order of what would break first:
#   * the model loads through Qwen2_5_VLForConditionalGeneration (the LLaVA class rejected the config);
#   * the processor accepts the chat-template prompt, and the padded sequence is a sane length
#     (Qwen2.5-VL uses dynamic resolution, so the count differs from LLaVA's 611 and max-len 2048 must hold);
#   * the image-token id is found, so label masking actually cuts the prompt (a wrong id would leave the
#     loss supervising the question as well as the caption);
#   * five steps run and the loss is finite.
# Offline flags are set: without them each load spends minutes retrying unreachable huggingface.co before
# falling back to the local cache, which wasted ten minutes earlier today.
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

echo "=== qwen runner present? ==="
grep -c "Qwen2_5_VLForConditionalGeneration" tools/_p1035_qwen_sites.py
grep -c "image_token_id" tools/_p1035_qwen_sites.py

echo "=== smoke: Qwen2.5-VL-7B, 5 steps, samples 20 ==="
rm -rf outputs/smoke_qwen2
$PY -u -X utf8 tools/_p1035_qwen_sites.py \
  --coco-root "$COCO" --precision bf16 --alloc-warmup-gb 1.5 \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/smoke_qwen2 > /root/p3/smoke_qwen2.out 2>&1
echo "exit=$?"
echo
echo "=== key lines ==="
grep -aE "model_type|load|parameters|batch tokens|sequence length|step [0-9]+/|epoch 1/1|held-out|Error|error" \
  /root/p3/smoke_qwen2.out | head -20
echo
echo "=== last lines if it failed ==="
tail -12 /root/p3/smoke_qwen2.out
echo QWEN_SMOKE_DONE
