#!/bin/bash
set -u
/root/miniconda3/bin/python - <<'PY'
from modelscope import snapshot_download
p = snapshot_download('lmms-lab/llava-onevision-qwen2-0.5b-ov', cache_dir='/root/autodl-tmp/ms')
print('LOO_PATH', p)
PY
echo FETCH_LOO_DONE
