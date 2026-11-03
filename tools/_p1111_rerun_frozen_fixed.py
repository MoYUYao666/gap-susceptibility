# -*- coding: utf-8 -*-
r"""Stop the running recomputation, upload the corrected script, and re-run the frozen arm.

The corrected script excludes the image tokens from the text side (`tools/_p1110`). The first thing to see is
whether the frozen number moves to a sane scale and whether it is still stable across batches -- that pair of
facts decides whether the other three arms are worth measuring.

    python tools/_p1111_rerun_frozen_fixed.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY = open(os.path.join(REPO, "tools", "_p1107_run_canonical.py"), encoding="utf-8").read()
SCRIPT = re.search(r"BODY = r'''(.*?)'''", BODY, re.S).group(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="frozen")
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

    def sh(cmd: str, timeout: int = 3000) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    print("  " + sh("pkill -9 -f _p1109.sh || true; pkill -9 -f _p1107_canonical.sh || true; sleep 3; "
                    "pgrep -c -f _p1107_canonical.sh || echo stopped"))
    sh("for i in $(seq 1 20); do u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits); "
       "[ \"$u\" -lt 2000 ] && break; sleep 5; done")
    print("  GPU now:", sh("nvidia-smi --query-gpu=memory.used --format=csv,noheader"))

    sftp = cli.open_sftp()
    with sftp.open("/root/p3/_p1107_canonical.sh", "w") as fh:
        fh.write(SCRIPT)
    sftp.close()
    print("  corrected script uploaded")

    print("=== verification that the mask excludes image tokens ===")
    print(sh("grep -n 'tok != IMG_ID' /root/p3/_p1107_canonical.sh | head -3"))

    print(f"\n=== recomputation: {a.arms} ===")
    print(sh(f"cd /root/p3 && ARMS={a.arms} EVAL_PAIRS=500 bash _p1107_canonical.sh 2>&1 "
             f"| grep -avE 'Loading weights' | tail -14"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
