#!/bin/bash
set -u
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1
echo "== remove cached VQA adapters so 1793-sample training really runs =="
rm -rf outputs/p3_vqa_adapters/r5_step outputs/p3_vqa_adapters/r6_step
echo "== VQA full 1793 per-step r5 $(date +%H:%M:%S) =="
$PY tools/vqa_downstream.py --rank 5 --train-samples 1793 --epochs 3 --eval-n 300 --per-step 2>&1 | tail -3
echo "== VQA full 1793 per-step r6 $(date +%H:%M:%S) =="
$PY tools/vqa_downstream.py --rank 6 --train-samples 1793 --epochs 3 --eval-n 300 --per-step 2>&1 | tail -3
echo "VQA_FULL_DONE $(date +%H:%M:%S)"
