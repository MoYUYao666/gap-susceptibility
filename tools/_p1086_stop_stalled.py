# -*- coding: utf-8 -*-
r"""Stop the two stalled fetches and report the multi-connection download's progress.

Two leftovers were still running: a `curl` of the COCO annotation archive at about 400 B/s (which would need
days) and a single-connection `curl -C -` for a weight shard at about 1 MB/s. Both are superseded -- the
weights are being fetched by the multi-connection fetcher at 13-16 MB/s, and the annotation archive will be
taken from a domestic source instead.

    python tools/_p1086_stop_stalled.py [--apply]
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

    def sh(cmd: str, timeout: int = 120) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    print("=== before ===")
    print(sh("ps -eo pid,etimes,cmd | grep -E 'curl' | grep -v grep | head -4 || echo none"))

    # kill the stalled annotation download and the single-connection weight fetch, not the multi-thread fetcher
    sh("pkill -9 -f 'annotations_trainval2014' || true")
    sh("pkill -9 -f 'curl -sSL -C -' || true")
    time.sleep(3)
    print("=== after ===")
    print(sh("ps -eo pid,etimes,cmd | grep -E 'curl' | grep -v grep | head -4 || echo none"))

    print("=== multi-connection fetcher still running? ===")
    print(sh("ps -eo pid,etimes,cmd | grep _p1083 | grep -v grep | head -2 || echo none"))
    print(sh("tail -3 /root/p3/mtdl.log 2>/dev/null | tr -d '\\r'"))
    print(sh("du -sh /root/autodl-tmp/modelscope 2>/dev/null"))

    # remove the partial annotation zip: it is useless at 3.8 MB and the source is being changed
    print("=== partial annotation archive ===")
    print(sh("ls -la /root/p3/coco_eval/_ann.zip 2>/dev/null || echo 'already gone'"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
