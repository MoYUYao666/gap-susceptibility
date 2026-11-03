#!/bin/bash
set -e
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/a3/hf
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
export TOKENIZERS_PARALLELISM=false
cd /root/autodl-tmp/a3
mkdir -p runs/logs logs
echo "[suite] start $(date)"
python cloud/run_cloud_suite.py --run --workers ${WORKERS:-2} --phases l14,fullcorpus
echo "[suite] verify"
python cloud/run_cloud_suite.py --verify
echo "[suite] done $(date)"
echo SUITE_DONE
