#!/usr/bin/env bash
# Diagnose the stalled install instead of waiting on it.
#
# Two pip processes sat at 0 B/s for minutes: the pytorch-index one was killed, and the mirror one
# (torch==2.9.1 + torchvision==0.24.1 from tuna) also stopped growing its cache and the root filesystem.
# The likely cause is that on PyPI `torch==2.9.1` is a CPU/cu126 build while the image already has
# 2.12.1+cu130, so pip is grinding through a conflict. This reports what pip is doing and what the image
# provides, so the next step is chosen on facts.
set -uo pipefail
PY=/root/miniconda3/bin/python

echo "=== pip process state (CPU time consumed, not just elapsed) ==="
ps -eo pid,etimes,time,stat,cmd | grep "pip install" | grep -v grep || echo none

echo "=== what the image already provides ==="
$PY - <<'PYEOF'
import torch, torchvision
print("  torch      ", torch.__version__, "cuda", torch.version.cuda, "avail", torch.cuda.is_available())
print("  torchvision", torchvision.__version__)
try:
    import torchvision.ops as ops
    print("  torchvision.ops imports and nms exists:", hasattr(ops, "nms"))
except Exception as exc:
    print("  torchvision.ops FAILED:", type(exc).__name__, exc)
PYEOF

echo "=== is pip actually working, or blocked on the network? ==="
timeout 8 strace -f -p "$(pgrep -f 'pip install.*tuna' | head -1)" -e trace=network -c 2>&1 | tail -5 \
  || echo "  (strace unavailable or no such process)"

echo "=== can it fetch a single wheel quickly? ==="
curl -sS -m 20 -o /dev/null -w '  tuna peft wheel: %{http_code} %{size_download} bytes %{speed_download} B/s\n' \
  "$($PY -m pip download --no-deps --dest /tmp/_probe peft==0.20.0 \
      --index-url https://pypi.tuna.tsinghua.edu.cn/simple -q 2>&1 >/dev/null; \
      echo https://pypi.tuna.tsinghua.edu.cn/simple/peft/)" 2>/dev/null || echo "  probe skipped"

echo "=== kill the stalled mirror install and test resolution without installing ==="
pkill -9 -f "pip install.*tuna" || true
sleep 2
$PY -m pip install --dry-run --no-deps --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    "torch==2.9.1" 2>&1 | tail -5
echo DIAG_DONE
