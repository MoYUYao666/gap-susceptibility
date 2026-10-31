# -*- coding: utf-8 -*-
r"""Push the patched sweep to the cloud and smoke-test bf16 with it.

The cloud still holds the sweep from the bundle, which predates `--precision` / `--deterministic` /
`--bench-steps` fixes, so a "bf16" run there would silently have been 4-bit. This uploads the current
sweep and runs five bf16 steps, printing the loss, the per-step time and the peak memory.

    python tools/_p978_cloud_push_sweep.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWEEP = os.path.join(REPO, "tools", "_p820_llava_sites.py")
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

SMOKE = r"""#!/usr/bin/env bash
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python

echo "=== sweep version in place ==="
grep -c "precision" tools/_p820_llava_sites.py
$PY tools/_p820_llava_sites.py --help 2>&1 | grep -A1 "precision" | head -3

echo "=== bf16 smoke: 5 steps ==="
rm -rf outputs/smoke_bf16
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root cloud_fixture --precision bf16 \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/smoke_bf16 2>&1 | grep -Ev "Loading weights|it/s\]" | tail -18

echo "=== peak memory during the run (recorded by the sweep process) ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
echo BF16_SMOKE_DONE
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
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    sftp = cli.open_sftp()
    sftp.put(SWEEP, "/root/p3/tools/_p820_llava_sites.py")
    with sftp.open("/root/p3/_smoke_bf16.sh", "w") as fh:
        fh.write(SMOKE)
    sftp.close()
    print(f"  uploaded sweep ({os.path.getsize(SWEEP)} bytes) and the smoke script")

    cli.exec_command("cd /root/p3 && chmod +x _smoke_bf16.sh && rm -f smoke_bf16.log && "
                     "setsid bash -c 'nohup bash _smoke_bf16.sh > smoke_bf16.log 2>&1' "
                     "< /dev/null > /dev/null 2>&1 & disown; sleep 1", timeout=30)
    time.sleep(200)
    _i, o, _e = cli.exec_command("cd /root/p3 && tail -30 smoke_bf16.log", timeout=120)
    print(o.read().decode("utf-8", "replace"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
