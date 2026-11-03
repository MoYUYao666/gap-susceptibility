# -*- coding: utf-8 -*-
r"""Install the pinned stack on the rented host and fetch the model there.

Pinned to what the local baseline used: python 3.12.14, torch 2.9.1 (cu130), transformers 5.16.1,
peft 0.20.0, bitsandbytes 0.50.2, accelerate 1.14.0, datasets 5.0.1, pillow 12.3.0, numpy 2.5.2.
The host's conda base is already python 3.12, so the versions can match closely; where a wheel is not
available the install fails loudly rather than silently substituting another version.

`HF_HOME` is pointed at the 50 GB data disk, because the root filesystem holds 30 GB and a 7B model with
its caches needs about 15-20 GB.

The install runs detached on the host and logs to `/root/p3/setup.log`, so it survives the SSH session and
can be polled.

    python tools/_p964_cloud_install.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
USER = os.environ.get("P3SSH_USER", "root")
PASS = os.environ.get("P3SSH_PASS", "")
REMOTE = "/root/p3"

INSTALL = r"""#!/usr/bin/env bash
set -uo pipefail
cd /root/p3
export HF_HOME=/root/autodl-tmp/hf
export PIP_CACHE_DIR=/root/autodl-tmp/pipcache
PY=/root/miniconda3/bin/python
PIP="/root/miniconda3/bin/python -m pip"

echo "=== host ==="; hostname; $PY -V; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
df -h / /root/autodl-tmp | tail -3

echo "=== pip mirrors ==="
$PIP config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple || true
$PIP config set global.trusted-host pypi.tuna.tsinghua.edu.cn || true

echo "=== install (pinned) ==="
$PIP install --no-input "numpy==2.5.2" "pillow==12.3.0" 2>&1 | tail -3
$PIP install --no-input "torch==2.9.1" --index-url https://download.pytorch.org/whl/cu130 2>&1 | tail -5
if ! $PY -c "import torch" 2>/dev/null; then
  echo "torch from the pytorch index failed; trying the mirror"
  $PIP install --no-input "torch==2.9.1" 2>&1 | tail -5
fi
$PIP install --no-input "transformers==5.16.1" "peft==0.20.0" "accelerate==1.14.0" \
     "bitsandbytes==0.50.2" "datasets==5.0.1" sentencepiece protobuf 2>&1 | tail -6

echo "=== version self-check ==="
$PY - <<'EOF'
import sys, importlib
want = {"torch": "2.9.1", "transformers": "5.16.1", "peft": "0.20.0",
        "bitsandbytes": "0.50.2", "accelerate": "1.14.0", "datasets": "5.0.1",
        "PIL": "12.3.0", "numpy": "2.5.2"}
bad = []
for name, ver in want.items():
    try:
        got = getattr(importlib.import_module(name), "__version__", "?")
    except Exception as exc:
        got = "MISSING (%s)" % type(exc).__name__
    ok = str(got).startswith(ver)
    print("  %-3s %-14s %s (want %s)" % ("OK" if ok else "BAD", name, got, ver))
    if not ok:
        bad.append(name)
import torch
print("  python", sys.version.split()[0], "| torch cuda", torch.version.cuda,
      "| device", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
print("  bf16 supported:", torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False)
if bad:
    print("VERSION MISMATCH:", ",".join(bad))
EOF

echo "=== model (server-side download, per project rule) ==="
export HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0
$PY - <<'EOF'
import os, time
from huggingface_hub import snapshot_download
t0 = time.time()
p = snapshot_download("llava-hf/llava-1.5-7b-hf")
print("  downloaded to", p, "in %.0f s" % (time.time() - t0))
print("  size %.1f GB" % (sum(os.path.getsize(os.path.join(r, f))
      for r, _d, fs in os.walk(p) for f in fs) / 1e9))
EOF

echo "=== disk after ==="
df -h / /root/autodl-tmp | tail -3
echo "SETUP_DONE"
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    if not a.apply:
        print("  (dry run)")
        return 0

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    sftp = cli.open_sftp()
    with sftp.open(f"{REMOTE}/install.sh", "w") as fh:
        fh.write(INSTALL)
    sftp.close()
    cmd = (f"cd {REMOTE} && chmod +x install.sh && "
           f"nohup bash install.sh > setup.log 2>&1 & echo started-pid $!")
    _in, out, err = cli.exec_command(cmd, timeout=60)
    print("  " + (out.read().decode() + err.read().decode()).strip())
    time.sleep(20)
    _in, out, _err = cli.exec_command(f"tail -12 {REMOTE}/setup.log", timeout=60)
    print("  --- setup.log so far ---")
    for line in out.read().decode("utf-8", "replace").splitlines():
        print(f"    {line}")
    cli.close()
    print("  install is running detached; poll with tools/_p965_cloud_poll.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
