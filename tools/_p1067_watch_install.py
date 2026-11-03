# -*- coding: utf-8 -*-
r"""Stop the stale installer, then measure how fast the mirror install is actually going.

The first setup script is still alive and keeps launching `pip install` against the stalled
`download.pytorch.org` index, so it has to be killed by name rather than by its child processes. Then the pip
cache growth over 45 s gives the real install rate, which decides whether to wait or change approach.

    python tools/_p1067_watch_install.py [--kill-old]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kill-old", action="store_true")
    ap.add_argument("--seconds", type=int, default=45)
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 240) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    if a.kill_old:
        sh("pkill -9 -f _p1062_cloud_setup_recompute || true")
        time.sleep(3)
        print("  stale installer:", sh("pgrep -af _p1062 || echo none"))

    def cache_bytes() -> int:
        raw = sh("du -sb /root/autodl-tmp/pipcache 2>/dev/null | cut -f1")
        return int(raw) if raw.strip().isdigit() else 0

    b1 = cache_bytes()
    time.sleep(a.seconds)
    b2 = cache_bytes()
    print(f"  pip cache: {b1 / 1e6:.0f} MB -> {b2 / 1e6:.0f} MB  "
          f"({(b2 - b1) / 1e6 / a.seconds:.2f} MB/s over {a.seconds}s)")

    print("  pip processes:")
    print(sh("ps -eo pid,etimes,cmd | grep 'pip install' | grep -v grep | head -3 || echo none"))
    print("  install.log tail:")
    print(sh("tail -8 /root/p3/install.log"))
    print("  disk:")
    print(sh("df -h / /root/autodl-tmp | tail -2"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
