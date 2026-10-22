#!/bin/bash
set -e
BASE=/root/autodl-tmp/p3work
mkdir -p $BASE/models $BASE/data $BASE/paper3/scripts $BASE/tools $BASE/outputs/analysis $BASE/outputs/p3_vqa_adapters $BASE/logs
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_DISABLE_XET=1
PY=/root/miniconda3/bin/python
$PY - <<'PY'
from huggingface_hub import snapshot_download
print(snapshot_download('llava-hf/llava-1.5-7b-hf', local_dir='/root/autodl-tmp/p3work/models/llava-hf'))
print(snapshot_download('flaviagiammarino/vqa-rad', repo_type='dataset', local_dir='/root/autodl-tmp/p3work/data/vqa_rad'))
PY
echo SETUP_DONE
