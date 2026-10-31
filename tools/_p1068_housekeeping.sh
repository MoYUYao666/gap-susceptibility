#!/usr/bin/env bash
# One housekeeping pass: drop the installer that is stuck on the slow index, verify the mirror install is
# advancing, and start the weight download with the HuggingFace transfer accelerator.
#
# Measured earlier on this host: download.pytorch.org stalled at 0 B/s while pypi.tuna.tsinghua.edu.cn ran at
# 3.12 MB/s, so any pip process still pointed at the pytorch index is pure noise and is removed here.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_HUB_DISABLE_XET=1
PY=/root/miniconda3/bin/python

echo "=== pip processes before ==="
ps -eo pid,etimes,cmd | grep "pip install" | grep -v grep || echo none

# kill only the ones using the stalled pytorch index
for pid in $(ps -eo pid,cmd | grep "pip install" | grep "download.pytorch.org" | grep -v grep | awk '{print $1}'); do
  echo "  killing $pid (stalled index)"
  kill -9 "$pid" 2>/dev/null || true
done
sleep 3

echo "=== pip processes after ==="
ps -eo pid,etimes,cmd | grep "pip install" | grep -v grep || echo none

echo "=== install progress (30 s on the pip cache and the root filesystem) ==="
C1=$(du -sb /root/autodl-tmp/pipcache 2>/dev/null | cut -f1 || echo 0)
R1=$(df --output=used / | tail -1 | tr -d ' ')
sleep 30
C2=$(du -sb /root/autodl-tmp/pipcache 2>/dev/null | cut -f1 || echo 0)
R2=$(df --output=used / | tail -1 | tr -d ' ')
echo "  pip cache:  $((C2/1000000)) MB -> $((C2/1000000)) MB (${C2} bytes)  delta $(( (C2-C1)/1000 )) KB/s"
echo "  root used:  $((R1/1000)) MB -> $((R2/1000)) MB   delta $(( (R2-R1)/1000 )) KB/s"

echo "=== start the LLaVA weight download in the background (hf_transfer) ==="
if [ -d "$HF_HOME/hub/models--llava-hf--llava-1.5-7b-hf" ]; then
  echo "  already present: $(du -sh "$HF_HOME/hub/models--llava-hf--llava-1.5-7b-hf" | cut -f1)"
else
  setsid bash -c "$PY - <<'PYEOF' > /root/p3/llava_dl.log 2>&1
import os, time
os.environ.setdefault('HF_HUB_ENABLE_HF_TRANSFER', '1')
from huggingface_hub import snapshot_download
t0 = time.time()
p = snapshot_download('llava-hf/llava-1.5-7b-hf', max_workers=8)
size = sum(os.path.getsize(os.path.join(r, f)) for r, _d, fs in os.walk(p) for f in fs)
dt = time.time() - t0
print('  size %.2f GB in %.0f s (%.2f MB/s)' % (size/1e9, dt, size/1e6/max(dt,1)))
print('LLAVA_DL_DONE')
PYEOF" < /dev/null > /dev/null 2>&1 &
  disown
  echo "  started; log at /root/p3/llava_dl.log"
fi

echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
echo HOUSEKEEPING_DONE
