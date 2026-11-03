#!/bin/bash
set -e
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/a3/hf
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
cd /root/autodl-tmp/a3
mkdir -p logs hf models data corpora runs
echo "[bootstrap] $(date)"
python cloud/fetch_weights.py
python cloud/bootstrap_data.py
python cloud/build_corpora.py
echo "[bootstrap] data and corpora ready $(date)"
echo BOOTSTRAP_DONE
