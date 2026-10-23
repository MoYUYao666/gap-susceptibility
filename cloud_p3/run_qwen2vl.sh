#!/bin/bash
set -u
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1
MODEL=/root/autodl-tmp/ms/models/Qwen--Qwen2-VL-2B-Instruct/snapshots/master
echo "== Qwen2-VL-2B r5 $(date +%H:%M:%S) =="
$PY paper3/scripts/run_training_qwen.py --rank 5 --seed 42 --epochs 3 --model-path $MODEL --tag qwen2vl 2>&1 | tail -4
echo "== Qwen2-VL-2B r6 $(date +%H:%M:%S) =="
$PY paper3/scripts/run_training_qwen.py --rank 6 --seed 42 --epochs 3 --model-path $MODEL --tag qwen2vl 2>&1 | tail -4
echo "QWEN2VL_DONE $(date +%H:%M:%S)"
