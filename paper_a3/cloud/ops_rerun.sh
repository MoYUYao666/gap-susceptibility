#!/bin/bash
set -e
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
cd /root/autodl-tmp/a3
echo "[rerun] start $(date)"
python cloud/run_cloud_suite.py --run --workers 2 --phases fullextra
python cloud/run_cloud_suite.py --verify
echo RERUN_DONE
