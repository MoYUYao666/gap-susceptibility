#!/usr/bin/env bash
# Fix the cloud environment: the image ships a torchvision built for a different torch, which breaks
# `import transformers` (RuntimeError: operator torchvision::nms does not exist) and with it `import peft`.
# The local baseline runs torchvision 0.24.1+cu130 against torch 2.9.1+cu130, so pin that pair.
set -uo pipefail
PY=/root/miniconda3/bin/python
PIP="$PY -m pip"

echo "=== before ==="
$PY - <<'EOF'
import importlib
for m in ("torch", "torchvision"):
    try:
        mod = importlib.import_module(m)
        print("  %-12s %s" % (m, getattr(mod, "__version__", "?")))
    except Exception as exc:
        print("  %-12s BROKEN: %s: %s" % (m, type(exc).__name__, str(exc)[:90]))
EOF

echo "=== install torchvision 0.24.1 for cu130 ==="
$PIP install --no-input "torchvision==0.24.1" --index-url https://download.pytorch.org/whl/cu130 2>&1 | tail -6

echo "=== after ==="
$PY - <<'EOF'
import importlib, traceback
ok = True
for m in ("torch", "torchvision", "transformers", "peft", "bitsandbytes", "accelerate"):
    try:
        mod = importlib.import_module(m)
        print("  %-14s %s" % (m, getattr(mod, "__version__", "?")))
    except Exception as exc:
        ok = False
        print("  %-14s BROKEN: %s" % (m, type(exc).__name__))
        traceback.print_exc()
print("ALL_IMPORTS_OK" if ok else "IMPORTS_STILL_BROKEN")
EOF
echo FIX_DONE
