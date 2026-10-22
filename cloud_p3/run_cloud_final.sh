#!/bin/bash
set -e
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1
echo "== extra env seeds r5 =="
$PY paper3/scripts/run_training.py --rank 5 --seed 123 --epochs 3 --num-samples 20 2>&1 | tail -3
$PY paper3/scripts/run_training.py --rank 5 --seed 789 --epochs 3 --num-samples 20 2>&1 | tail -3
echo "== extra env seeds r6 =="
$PY paper3/scripts/run_training.py --rank 6 --seed 123 --epochs 3 --num-samples 20 2>&1 | tail -3
$PY paper3/scripts/run_training.py --rank 6 --seed 789 --epochs 3 --num-samples 20 2>&1 | tail -3
echo "== VQA full VQA-RAD (1793 train pairs), per-step =="
$PY tools/vqa_prepare.py
$PY tools/vqa_downstream.py --rank base --eval-n 200 2>&1 | tail -3
$PY tools/vqa_downstream.py --rank 5 --train-samples 1793 --epochs 3 --eval-n 200 --per-step 2>&1 | tail -3
$PY tools/vqa_downstream.py --rank 6 --train-samples 1793 --epochs 3 --eval-n 200 --per-step 2>&1 | tail -3
echo "CLOUD_FINAL_DONE"
