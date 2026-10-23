#!/bin/bash
set -u
/root/miniconda3/bin/python - <<'PY'
from modelscope import snapshot_download
p = snapshot_download('Qwen/Qwen2-VL-2B-Instruct', cache_dir='/root/autodl-tmp/ms')
print('QWEN2VL_PATH', p)
PY
echo FETCH_QWEN2VL_DONE
