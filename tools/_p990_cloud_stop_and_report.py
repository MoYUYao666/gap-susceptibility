# -*- coding: utf-8 -*-
r"""Stop the cloud run and report exactly what is on the host, without shutting it down.

Operator decision 2026-10-15: "那就不跑了，等super有机子了再跑" -- wait for a bigger device rather than force
bf16 onto a 24 GB card. So: stop anything running, record the state for a clean restart later, and leave the
machine's power to the operator (they control billing; stopping it from here was never requested for this
host).

    python tools/_p990_cloud_stop_and_report.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

STOP = r"""
echo "=== processes before ==="
pgrep -af "_p820_llava_sites|_p98[0-9]_cloud|_p989" | head -6 || echo "  none"
pkill -9 -f _p820_llava_sites || true
pkill -9 -f _p989_cloud_4090_sweep || true
sleep 6
echo "=== processes after ==="
pgrep -af "_p820_llava_sites" | head -3 || echo "  none"
echo "=== gpu ==="
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
echo "=== what the run left behind ==="
ls -la /root/p3/outputs/ 2>/dev/null
for d in /root/p3/outputs/*/; do echo "  $d: $(ls "$d" 2>/dev/null | wc -l) files"; done
echo "=== preserved assets ==="
ls /root/p3/coco_full/val2014 | wc -l
du -sh /root/p3/coco_full /root/autodl-tmp/hf /root/p3/tools 2>/dev/null
echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
echo STOP_DONE
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    if a.apply:
        _i, o, e = cli.exec_command(STOP, timeout=300)
        print((o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip())
    else:
        _i, o, _e = cli.exec_command("nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
                                     "pgrep -af _p820_llava_sites | head -3", timeout=60)
        print("  (dry run) current state:\n" + o.read().decode("utf-8", "replace"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
