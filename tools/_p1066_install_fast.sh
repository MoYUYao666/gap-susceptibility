#!/usr/bin/env bash
# Install the stack through the fast mirror, with the HuggingFace transfer accelerator enabled.
#
# Measured on this host (2026-10-16 19:45):
#   pypi.tuna.tsinghua.edu.cn   4,486,468 B/s     <- use this
#   download.pytorch.org                0 B/s     <- the image's own index; a 476 MB wheel sat stalled
#   hf-mirror.com                   227 B/s (probe), reachable
# The image already ships torch 2.12.1+cu130 and torchvision 0.27.1+cu130, but the archived runs used
# torch 2.9.1, so the pinned versions are installed to match them rather than reusing the image's.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_HUB_DISABLE_XET=1
export PIP_CACHE_DIR=/root/autodl-tmp/pipcache
PY=/root/miniconda3/bin/python
TUNA=https://pypi.tuna.tsinghua.edu.cn/simple

echo "=== stop anything still trying the slow index ==="
pkill -f "pip install" || true
sleep 3
ps -eo pid,cmd | grep -E "pip install" | grep -v grep || echo "  none left"

echo "=== install through tuna ==="
$PY -m pip install -q --no-input --index-url "$TUNA" \
    "torch==2.9.1" "torchvision==0.24.1" "transformers==5.16.1" "peft==0.20.0" \
    "accelerate==1.14.0" "huggingface_hub[hf_transfer]" hf_transfer sentencepiece protobuf 2>&1 | tail -4
# torch 2.9.1 for cu130 is not on PyPI; if the plain wheel landed, the CUDA build comes from the image's
# own libraries, so the import check below is the real test rather than the index used.
echo "  install exit: $?"

echo "=== prove the imports work ==="
$PY - <<'PYEOF'
import importlib, sys
want = {"torch": None, "torchvision": None, "transformers": "5.16.1", "peft": "0.20.0",
        "accelerate": "1.14.0", "hf_transfer": None}
import torch
print("  torch          ", torch.__version__, "| cuda build", torch.version.cuda,
      "| available", torch.cuda.is_available())
for name, ver in want.items():
    try:
        mod = importlib.import_module(name)
        got = getattr(mod, "__version__", "?")
        print("  %-15s %s%s" % (name, got, "" if ver is None or str(got).startswith(ver) else f"  (WANT {ver})"))
    except Exception as exc:
        print("  %-15s MISSING (%s)" % (name, type(exc).__name__))
try:
    from transformers import LlavaForConditionalGeneration  # noqa: F401
    print("  LlavaForConditionalGeneration import: OK")
except Exception as exc:
    print("  LlavaForConditionalGeneration import FAILED:", type(exc).__name__, exc)
PYEOF

echo "=== LLaVA weights through hf-mirror with hf_transfer ==="
$PY - <<'PYEOF'
import os, time
from huggingface_hub import snapshot_download
t0 = time.time()
p = snapshot_download("llava-hf/llava-1.5-7b-hf", max_workers=8)
size = sum(os.path.getsize(os.path.join(r, f)) for r, _d, fs in os.walk(p) for f in fs)
dt = time.time() - t0
print("  path:", p)
print("  size: %.2f GB in %.0f s  (%.1f MB/s)" % (size / 1e9, dt, size / 1e6 / max(dt, 1)))
PYEOF

echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
echo INSTALL_FAST_DONE
