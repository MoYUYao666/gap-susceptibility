#!/usr/bin/env bash
# Pull the weights from the repository that actually exists, and install the inference stack alongside it.
#
# The listing showed `llava-hf/llava-1.5-7b-hf` present on ModelScope (18 files, 14.13 GB) while the guessed
# `AI-ModelScope/llava-1.5-7b-hf` does not exist. Both the model fetch and the package install run in the
# background here so they overlap, and the log records the achieved download rate.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export MODELSCOPE_CACHE=/root/autodl-tmp/modelscope
export HF_HOME=/root/autodl-tmp/hf
PY=/root/miniconda3/bin/python

echo "=== install the inference stack from tuna (transformers/peft/accelerate) ==="
$PY -m pip install -q --no-input -i https://pypi.tuna.tsinghua.edu.cn/simple \
    "transformers==5.16.1" "peft==0.20.0" "accelerate==1.14.0" sentencepiece protobuf 2>&1 | tail -3
$PY -c "
import importlib
for m in ('transformers','peft','accelerate'):
    try:
        print('  %-14s %s' % (m, importlib.import_module(m).__version__))
    except Exception as e:
        print('  %-14s MISSING %s' % (m, type(e).__name__))
"

echo "=== download weights (background) ==="
setsid bash -c "$PY - <<'PYEOF' > /root/p3/ms_llava_dl.log 2>&1
import os, time
from modelscope import snapshot_download
t0 = time.time()
p = snapshot_download('llava-hf/llava-1.5-7b-hf', cache_dir='/root/autodl-tmp/modelscope')
size = sum(os.path.getsize(os.path.join(r, f)) for r, _d, fs in os.walk(p) for f in fs)
dt = time.time() - t0
print('  path:', p)
print('  size %.2f GB in %.0f s (%.2f MB/s)' % (size/1e9, dt, size/1e6/max(dt,1)))
print('MS_LLAVA_DONE')
PYEOF" < /dev/null > /dev/null 2>&1 &
disown
sleep 40
echo "=== download progress after 40 s ==="
du -sh /root/autodl-tmp/modelscope 2>/dev/null || echo "  0"
tail -3 /root/p3/ms_llava_dl.log 2>/dev/null || echo "  no log yet"

echo "=== disk ==="
df -h /root/autodl-tmp | tail -1
echo MS_START_DONE
