#!/bin/bash
set -e
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1
$PY tools/vqa_prepare.py
$PY tools/vqa_downstream.py --rank base --eval-n 50 2>&1 | tail -3
$PY tools/vqa_downstream.py --rank 5 --train-samples 80 --epochs 3 --eval-n 50 2>&1 | tail -3
$PY tools/vqa_downstream.py --rank 6 --train-samples 80 --epochs 3 --eval-n 50 2>&1 | tail -3
echo VQA_DONE
