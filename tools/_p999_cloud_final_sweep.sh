#!/usr/bin/env bash
# The full bf16 sweep, with the only speed change that leaves the experiment untouched: the held-out
# measurement runs 32 pairs per forward instead of 2.
#
# Measured 2026-10-16 on this host, 25 steps each, to justify not going further:
#   batch 2  0.9-1.0 s/step   1214 tokens/step   0.500 s per sample
#   batch 4  1.9 s/step       2444 tokens/step   0.475 s per sample
#   batch 8  4.0 s/step       4928 tokens/step   0.500 s per sample
#   TF32     no change at all (bf16 weights never take the fp32 matmul path)
# So the step cost is the weight traffic, not the batch, and the training batch stays at 2 -- every sample,
# every epoch and every seed is unchanged. The measurement is no_grad work, so its batch is free to differ.
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

echo "=== clear the device and confirm the memory is back ==="
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 40); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting: ${used} MiB"; sleep 10
done
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

echo "=== sweep version and fixture ==="
$PY -c "import io,ast;s=io.open('tools/_p820_llava_sites.py',encoding='utf-8').read();ast.parse(s);print('  parses | eval-batch', '--eval-batch' in s, '| tf32', '--tf32' in s, '| precision', '--precision' in s)"
ls "$COCO/val2014" | wc -l
[ -f "$COCO/annotations/captions_val2014.json" ] || cp "$COCO/annotations/captions_run.json" "$COCO/annotations/captions_val2014.json"

echo "=== full sweep: bf16, 1500 train / 500 held out, batch 2, eval-batch 32, 3 epochs, 3 seeds, 4 arms ==="
rm -rf outputs/llava_bf16_sites
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --eval-batch 32 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites 2>&1 | grep -Ev "Loading weights|it/s\]"
echo BF16_SWEEP_DONE
