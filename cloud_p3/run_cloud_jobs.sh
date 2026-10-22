#!/bin/bash
set -e
BASE=/root/autodl-tmp/p3work
cd $BASE
PY=/root/miniconda3/bin/python
export HF_HUB_OFFLINE=1
echo "== hardware repro r5 =="
$PY paper3/scripts/run_training.py --rank 5 --seed 42 --epochs 3 --num-samples 20 2>&1 | tail -4
echo "== hardware repro r6 =="
$PY paper3/scripts/run_training.py --rank 6 --seed 42 --epochs 3 --num-samples 20 2>&1 | tail -4
echo "== vqa prepare =="
$PY tools/vqa_prepare.py
echo "== vqa base =="
$PY tools/vqa_downstream.py --rank base --eval-n 50 2>&1 | tail -3
echo "== vqa r5 =="
$PY tools/vqa_downstream.py --rank 5 --train-samples 80 --epochs 3 --eval-n 50 2>&1 | tail -3
echo "== vqa r6 =="
$PY tools/vqa_downstream.py --rank 6 --train-samples 80 --epochs 3 --eval-n 50 2>&1 | tail -3
echo "== qwen2.5-7b r5 =="
$PY paper3/scripts/run_training_qwen25.py --rank 5 --seed 42 --epochs 3 --model-path /root/autodl-tmp/hf/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/main --tag cloud_q25_7b_r5 2>&1 | tail -3
echo "== qwen2.5-7b r6 =="
$PY paper3/scripts/run_training_qwen25.py --rank 6 --seed 42 --epochs 3 --model-path /root/autodl-tmp/hf/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/main --tag cloud_q25_7b_r6 2>&1 | tail -3
echo "== qwen2.5-7b r5 seed123 =="
$PY paper3/scripts/run_training_qwen25.py --rank 5 --seed 123 --epochs 3 --model-path /root/autodl-tmp/hf/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/main --tag cloud_q25_7b_r5_s123 2>&1 | tail -3
echo "== qwen2.5-7b r6 seed123 =="
$PY paper3/scripts/run_training_qwen25.py --rank 6 --seed 123 --epochs 3 --model-path /root/autodl-tmp/hf/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/main --tag cloud_q25_7b_r6_s123 2>&1 | tail -3
echo "JOBS_DONE"
