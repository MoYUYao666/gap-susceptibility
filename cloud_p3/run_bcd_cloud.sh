#!/bin/bash
set -e
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1
mkdir -p data/marine_captions paper3/scripts/outputs/experiments outputs/analysis outputs/p3_vqa_adapters
unzip -o -q marine_captions.zip -d data/marine_captions
echo "== C1: 10 seeds x ranks 4-7 =="
for r in 4 5 6 7; do
  for s in 42 123 456 789 999 1024 7 17 27 37; do
    $PY paper3/scripts/run_training.py --rank $r --seed $s --epochs 3 --num-samples 20 >/dev/null 2>&1
  done
done
echo "== B2: high-rank run + curvature =="
$PY paper3/scripts/run_training.py --rank 24 --seed 42 --epochs 3 --num-samples 20 2>&1 | tail -2
$PY tools/hessian_probe.py --rank 24 2>&1 | tail -3
echo "== D3: real-image sweep ranks 4-8 =="
for r in 4 5 6 7 8; do
  $PY paper3/scripts/run_training.py --rank $r --seed 42 --epochs 3 --num-samples 20 --data-path paper3/train-caption-00000.parquet --images-dir data/marine_captions >/dev/null 2>&1
done
echo "== A2: VQA 400 per-step =="
$PY tools/vqa_downstream.py --rank base --eval-n 200 2>&1 | tail -2
$PY tools/vqa_downstream.py --rank 5 --train-samples 400 --epochs 3 --eval-n 200 --per-step 2>&1 | tail -2
$PY tools/vqa_downstream.py --rank 6 --train-samples 400 --epochs 3 --eval-n 200 --per-step 2>&1 | tail -2
echo "BCD_CLOUD_DONE"
