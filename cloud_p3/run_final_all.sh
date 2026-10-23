#!/bin/bash
# Final cloud batch for the remaining A/B/C/D items. Runs sequentially on one GPU, writes a log per block.
# Usage (after uploading this repo state):
#   cd /root/autodl-tmp/p3work && nohup bash run_final_all.sh > final_all.log 2>&1 &
set -u
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1

step () { echo "===== $1 $(date +%H:%M:%S) ====="; }

step "C1 r3/r8 ten seeds"
for r in 3 8; do
  for s in 42 123 456 789 999 1024 7 17 27 37; do
    $PY paper3/scripts/run_training.py --rank $r --seed $s --epochs 3 --num-samples 20 >/dev/null 2>&1 || echo "FAIL r$r s$s"
  done
done
echo "C1 DONE"

step "D3 real-image extra seeds"
for s in 123 789; do
  for r in 5 6; do
    $PY paper3/scripts/run_training.py --rank $r --seed $s --epochs 3 --num-samples 20 \
      --data-path paper3/train-caption-00000.parquet --images-dir data/marine_captions >/dev/null 2>&1 \
      || echo "FAIL d3 r$r s$s"
  done
done
echo "D3 DONE"

step "D4 dolly instruction family"
$PY prep_dolly.py 2>/dev/null || $PY tools/prep_dolly.py 2>/dev/null || echo "FAIL dolly prep"
if [ -f paper3/train-dolly-00000.parquet ]; then
  for r in 4 5 6 7; do
    for s in 42 123; do
      $PY paper3/scripts/run_training.py --rank $r --seed $s --epochs 3 --num-samples 20 \
        --data-path paper3/train-dolly-00000.parquet >/dev/null 2>&1 || echo "FAIL d4 r$r s$s"
    done
  done
fi
echo "D4 DONE"

step "A2 full VQA-RAD per-step"
$PY tools/vqa_prepare.py
$PY tools/vqa_downstream.py --rank base --eval-n 300 2>&1 | tail -2
$PY tools/vqa_downstream.py --rank 5 --train-samples 1793 --epochs 3 --eval-n 300 --per-step 2>&1 | tail -2
$PY tools/vqa_downstream.py --rank 6 --train-samples 1793 --epochs 3 --eval-n 300 --per-step 2>&1 | tail -2
echo "A2 DONE"

step "D1 third VLM family (best effort)"
if [ -f tools/loo_run.py ]; then
  timeout 3600 $PY tools/loo_run.py 2>&1 | tail -5 || echo "D1 FAILED/legacy"
else
  echo "D1 skipped (runner not uploaded)"
fi
echo "ALL DONE $(date +%H:%M:%S)"
