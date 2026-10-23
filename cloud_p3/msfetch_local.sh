#!/bin/bash
set -e
/root/miniconda3/bin/pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple modelscope 2>&1 | tail -1 || true
/root/miniconda3/bin/python - <<'PY'
from modelscope import snapshot_download
p = snapshot_download('llava-hf/llava-1.5-7b-hf', cache_dir='/root/autodl-tmp/ms')
print('SNAPSHOT', p)
PY
mkdir -p /root/autodl-tmp/p3work/models
rm -rf /root/autodl-tmp/p3work/models/llava-hf
ln -sfn /root/autodl-tmp/ms/models/llava-hf--llava-1.5-7b-hf/snapshots/master /root/autodl-tmp/p3work/models/llava-hf
echo MSFETCH_DONE
