# -*- coding: utf-8 -*-
r"""Start the COCO fixture fetch on the host and report the weight download's progress.

Kept as a file because the nested quoting of an inline command got mangled by PowerShell again.

    python tools/_p1106_start_coco.py [--apply]
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
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
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

    launch = ("cd /root/p3 && setsid bash -c 'nohup bash tools/_p1105_coco_mt.sh > coco_mt.log 2>&1' "
              "< /dev/null > /dev/null 2>&1 & echo launched")
    print("  " + sh(launch))
    time.sleep(45)

    print("=== coco_mt.log ===")
    print(sh("tail -8 /root/p3/coco_mt.log 2>/dev/null | tr -d '\\r' || echo 'no log yet'"))
    print("=== weights ===")
    print(sh("tail -3 /root/p3/mirror_mt.log 2>/dev/null | tr -d '\\r'"))
    print("=== disk ===")
    print(sh("df -h / /root/autodl-tmp | tail -2; du -sh /root/autodl-tmp/hf 2>/dev/null"))
    print("=== adapters on the host ===")
    print(sh("ls /root/p3/adapters/ | wc -l; du -sh /root/p3/adapters"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
