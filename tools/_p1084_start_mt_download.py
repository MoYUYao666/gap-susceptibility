# -*- coding: utf-8 -*-
r"""Upload the multi-connection fetcher and start it on the host.

Split out from the shell one-liners because PowerShell mangled the quoting of an inline command twice in a row.

    python tools/_p1084_start_mt_download.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import paramiko

REPO = Path(__file__).resolve().parents[1]
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
DEST = "/root/autodl-tmp/modelscope/hub/llava-hf/llava-1.5-7b-hf"


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
    sftp = cli.open_sftp()
    local = REPO / "tools" / "_p1083_parallel_fetch.py"
    sftp.put(str(local), "/root/p3/tools/_p1083_parallel_fetch.py")
    size = sftp.stat("/root/p3/tools/_p1083_parallel_fetch.py").st_size
    sftp.close()
    print(f"  uploaded fetcher ({size} bytes)")

    def sh(cmd: str, timeout: int = 180) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    # stop the old single-connection attempts
    sh("pkill -9 -f _p1082.sh || true; pkill -9 -f 'curl -sSL -C' || true; sleep 2")
    print("  stopped the previous downloaders")

    launch = ("cd /root/p3 && setsid bash -c 'nohup /root/miniconda3/bin/python "
              "tools/_p1083_parallel_fetch.py "
              f"--dest {DEST} > mtdl.log 2>&1' < /dev/null > /dev/null 2>&1 & echo started")
    print("  " + sh(launch))
    time.sleep(60)
    print("=== mtdl.log after 60 s ===")
    print(sh("tail -12 /root/p3/mtdl.log 2>/dev/null | tr -d '\\r' || echo 'no log'"))
    print("=== disk ===")
    print(sh("df -h /root/autodl-tmp | tail -1; du -sh /root/autodl-tmp/modelscope 2>/dev/null"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
