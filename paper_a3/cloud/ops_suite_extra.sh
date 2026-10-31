#!/bin/bash
set -e
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
cd /root/autodl-tmp/a3
echo "[extra] start $(date)"
python cloud/run_cloud_suite.py --run --workers 3 --phases fullextra,l14nwpu
echo "[extra] verify"
python cloud/run_cloud_suite.py --verify
echo EXTRA_DONE
