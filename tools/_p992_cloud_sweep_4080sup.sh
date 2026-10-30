#!/usr/bin/env bash
# Full bf16 sweep on the third host (RTX 4080 SUPER, 32.8 GB), where the environment and the 2000-image
# fixture survived the restart, so nothing is reinstalled.
#
# Expected memory: the first host of this same model peaked at 29.95 GB with this configuration and this
# device reports 32,760 MiB, so bf16 fits without any extra flag. The `--alloc-warmup-gb` option added for
# the 24 GB attempt is not present in the sweep on this host and is not passed here; the run below is the
# same configuration that succeeded on the first host.
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

echo "=== clear the device and confirm the memory is really back ==="
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 30); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  echo "  wait $i: ${used} MiB"
  [ "$used" -lt 2000 ] && break
  sleep 10
done
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

echo "=== fixture and sweep version ==="
ls "$COCO/val2014" | wc -l
[ -f "$COCO/annotations/captions_val2014.json" ] || cp "$COCO/annotations/captions_run.json" "$COCO/annotations/captions_val2014.json"
$PY -c "import io;s=io.open('tools/_p820_llava_sites.py',encoding='utf-8').read();print('  --precision present:', '--precision' in s, '| --report-every present:', '--report-every' in s)"

echo "=== full sweep: bf16, 1500 train / 500 held out, 3 epochs, 3 seeds, 4 arms ==="
rm -rf outputs/llava_bf16_sites
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites 2>&1 | grep -Ev "Loading weights|it/s\]"
echo BF16_SWEEP_DONE
