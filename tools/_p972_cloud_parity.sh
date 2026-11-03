#!/usr/bin/env bash
# Cloud parity run: the same command that produced the local baseline, on the same fixture.
# Local result: loss 2.9466 at step 5 (a repeat gave 2.9449, so the tolerance is 5e-3).
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python

echo "=== device ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
$PY -V
echo "=== model cached? ==="
du -sh "$HF_HOME/hub/models--llava-hf--llava-1.5-7b-hf" 2>/dev/null || echo "NOT CACHED"

echo "=== parity run (20 pairs / 10 held-out / 5 steps, 4-bit, as locally) ==="
# The bundle carried outputs/ from the local machine, which included a record for exactly this
# configuration -- so the first attempt hit the sweep's "already complete, skipping" branch and trained
# nothing. The output directory is cleared here; the skip logic is right for the real sweep and wrong for
# a parity run.
rm -rf outputs/llava_parity_cloud
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root cloud_fixture \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/llava_parity_cloud 2>&1 | grep -Ev "Loading weights|it/s\]" | tail -40
echo PARITY_DONE
