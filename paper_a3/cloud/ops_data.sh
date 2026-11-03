#!/bin/bash
set -e
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
cd /root/autodl-tmp/a3
mkdir -p logs data corpora
echo "[data] start $(date)"
python cloud/bootstrap_data2.py
python cloud/build_corpora.py
echo "[data] done $(date)"
df -h /root/autodl-tmp | tail -1
echo DATA_DONE
