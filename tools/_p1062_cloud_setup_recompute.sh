#!/usr/bin/env bash
# Set up the new host for the metric recomputation: the same pinned stack that produced the archived runs,
# minus nothing that matters, plus the LLaVA weights.
#
# This host is a fresh instance, so nothing is preinstalled. The pins are the ones established on the earlier
# hosts (torchvision in particular must match torch, or `import transformers` fails with
# "operator torchvision::nms does not exist" while every version number looks correct).
#
# Only forward passes are needed for the recomputation, so no training dependencies are installed.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
export PIP_CACHE_DIR=/root/autodl-tmp/pipcache
PY=/root/miniconda3/bin/python

echo "=== before ==="
df -h / /root/autodl-tmp | tail -2
$PY -V

echo "=== pinned stack ==="
$PY -m pip install -q --no-input "numpy==2.5.2" "pillow==12.3.0" 2>&1 | tail -2
$PY -m pip install -q --no-input "torch==2.9.1" --index-url https://download.pytorch.org/whl/cu130 2>&1 | tail -2
# torchvision MUST match torch: the image's own build breaks transformers with
# "RuntimeError: operator torchvision::nms does not exist".
$PY -m pip install -q --no-input "torchvision==0.24.1" --index-url https://download.pytorch.org/whl/cu130 2>&1 | tail -2
$PY -m pip install -q --no-input "transformers==5.16.1" "peft==0.20.0" "accelerate==1.14.0" \
    sentencepiece protobuf 2>&1 | tail -3

echo "=== prove the imports work (versions alone are not enough) ==="
$PY - <<'PYEOF'
import importlib, sys
want = {"torch": "2.9.1", "torchvision": "0.24.1", "transformers": "5.16.1", "peft": "0.20.0",
        "accelerate": "1.14.0"}
bad = []
for name, ver in want.items():
    try:
        got = getattr(importlib.import_module(name), "__version__", "?")
    except Exception as exc:
        got = "BROKEN:%s" % type(exc).__name__
    ok = str(got).startswith(ver)
    print("  %-3s %-14s %s (want %s)" % ("OK" if ok else "BAD", name, got, ver))
    if not ok:
        bad.append(name)
import torch
print("  cuda available:", torch.cuda.is_available(),
      "| device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")
if bad:
    sys.exit("IMPORTS BROKEN: " + ",".join(bad))
print("ALL_IMPORTS_OK")
PYEOF

echo "=== LLaVA weights (server-side download, 13 GB) ==="
$PY - <<'PYEOF'
import os, time
from huggingface_hub import snapshot_download
t0 = time.time()
p = snapshot_download("llava-hf/llava-1.5-7b-hf")
size = sum(os.path.getsize(os.path.join(r, f)) for r, _d, fs in os.walk(p) for f in fs)
print("  path:", p)
print("  size: %.1f GB in %.0f s" % (size / 1e9, time.time() - t0))
PYEOF

echo "=== after ==="
df -h / /root/autodl-tmp | tail -2
echo SETUP_DONE
