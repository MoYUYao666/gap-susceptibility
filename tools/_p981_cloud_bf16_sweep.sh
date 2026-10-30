#!/usr/bin/env bash
# The full sweep on the rented device, in bf16 (no 4-bit quantisation) with a larger training set.
#
# Operator instruction 2026-10-15: "不要4bit量化，就原模型直接跑，多跑一点".
#   - precision bf16: the 32.8 GB device holds the 7B weights natively, so the dequantisation rounding
#     of 4-bit is not needed. Measured difference at the end of a 5-step parity run: DG* moves -0.911%
#     in bf16 against -1.067% in 4-bit, i.e. about 0.15 percentage points.
#   - more data: 1500 training pairs and 500 held out, against 400/300 in the published configuration.
#     The larger set is built from the same official COCO val2014 order, so ids 1..1500 are a superset of
#     the local baseline's 400 and the smaller run stays directly comparable.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python

COCO=/root/p3/coco_full
# The sweep reads annotations/captions_val2014.json. The trimmed file on the host is called
# captions_run.json (an earlier rename), so whichever of the two exists is copied into place; the script
# reports what it found instead of assuming.
if [ -f "$COCO/annotations/captions_run.json" ]; then
  cp -f "$COCO/annotations/captions_run.json" "$COCO/annotations/captions_val2014.json"
  echo "  annotations: used captions_run.json"
elif [ -f "$COCO/annotations/captions_first2000.json" ]; then
  cp -f "$COCO/annotations/captions_first2000.json" "$COCO/annotations/captions_val2014.json"
  echo "  annotations: used captions_first2000.json"
else
  echo "  annotations: NONE FOUND -- listing the directory"
  ls -la "$COCO/annotations/"
  exit 1
fi
ls -la "$COCO/annotations/" | tail -4

echo "=== device ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo "=== fixture ==="
ls "$COCO/val2014" | wc -l; du -sh "$COCO/val2014"
echo "=== sweep: bf16, 1500 train / 500 held out, 3 epochs, 3 seeds, 4 arms ==="
rm -rf outputs/llava_bf16_sites
# No `tee` in the pipeline: it buffers, so the heartbeat lines stayed invisible while the run was going
# (observed 2026-10-15 23:25, log 0 bytes while the GPU was at 100%). The log is the file the whole
# script already writes to, and the sweep flushes every heartbeat.
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 \
  --samples 1500 --eval-pairs 500 --epochs 3 \
  --batch 2 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites 2>&1 | grep -Ev "Loading weights|it/s\]"
echo BF16_SWEEP_DONE
