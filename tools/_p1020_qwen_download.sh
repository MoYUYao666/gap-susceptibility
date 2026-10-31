#!/usr/bin/env bash
# Fetch Qwen2.5-VL-7B onto the data disk while the LLaVA sweep keeps the GPU busy.
#
# The download is I/O and network work, so it runs alongside training without competing for the device. It is
# fetched on the server, per the project rule that model weights are never uploaded from the laptop.
set -uo pipefail
cd /root/p3
export HF_HOME=/root/autodl-tmp/hf
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
export HF_HUB_DISABLE_PROGRESS_BARS=1
PY=/root/miniconda3/bin/python

echo "=== before ==="
df -h /root/autodl-tmp | tail -1
du -sh "$HF_HOME/hub" 2>/dev/null

echo "=== downloading Qwen/Qwen2.5-VL-7B-Instruct ==="
$PY - <<'PYEOF'
import os, time
from huggingface_hub import snapshot_download
t0 = time.time()
p = snapshot_download("Qwen/Qwen2.5-VL-7B-Instruct")
size = sum(os.path.getsize(os.path.join(r, f)) for r, _d, fs in os.walk(p) for f in fs)
print("  path:", p)
print("  size: %.1f GB" % (size / 1e9))
print("  took: %.0f s" % (time.time() - t0))
PYEOF

echo "=== after ==="
df -h /root/autodl-tmp | tail -1
du -sh "$HF_HOME/hub"/* 2>/dev/null
echo QWEN_DOWNLOAD_DONE
