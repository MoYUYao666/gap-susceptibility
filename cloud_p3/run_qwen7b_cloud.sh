#!/bin/bash
set -e
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1
QWEN=/root/autodl-tmp/hf/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/main
$PY paper3/scripts/run_training_qwen25.py --rank 5 --seed 42 --epochs 3 --model-path $QWEN --tag cloud_q25_7b_r5 2>&1 | tail -3
$PY paper3/scripts/run_training_qwen25.py --rank 6 --seed 42 --epochs 3 --model-path $QWEN --tag cloud_q25_7b_r6 2>&1 | tail -3
$PY paper3/scripts/run_training_qwen25.py --rank 5 --seed 123 --epochs 3 --model-path $QWEN --tag cloud_q25_7b_r5_s123 2>&1 | tail -3
$PY paper3/scripts/run_training_qwen25.py --rank 6 --seed 123 --epochs 3 --model-path $QWEN --tag cloud_q25_7b_r6_s123 2>&1 | tail -3
echo QWEN7B_DONE
