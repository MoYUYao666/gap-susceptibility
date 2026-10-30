# -*- coding: utf-8 -*-
r"""Compare the local and remote copies of the sweep, feature by feature.

Uploads are not trusted here: earlier in this session an upload raced a momentarily broken file, and a
local-only parse check reported success. This prints the size and the presence of each option on both sides.

    python tools/_p1003_compare_sweep.py
"""
from __future__ import annotations

import os
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = os.path.join(REPO, "tools", "_p820_llava_sites.py")
REMOTE = "/root/p3/tools/_p820_llava_sites.py"
FLAGS = ("--precision", "--deterministic", "--coco-root", "--bench-steps", "--report-every",
         "--out-dir", "--eval-batch", "--tf32", "--alloc-warmup-gb", "--resume")

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")


def main() -> int:
    local = open(LOCAL, encoding="utf-8").read()
    print(f"  local : {len(local)} bytes")
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set; remote side skipped")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    sftp = cli.open_sftp()
    remote = sftp.open(REMOTE, "r").read().decode("utf-8", "replace")
    sftp.close()
    cli.close()
    print(f"  remote: {len(remote)} bytes")
    print(f"  identical: {local == remote}")
    print(f"  {'flag':<20} {'local':>6} {'remote':>7}")
    ok = True
    for f in FLAGS:
        l, r = f in local, f in remote
        if l != r:
            ok = False
        print(f"  {f:<20} {str(l):>6} {str(r):>7}")
    print("  " + ("BOTH SIDES AGREE" if ok else "MISMATCH -- sync before running"))
    return 0 if ok and local == remote else 1


if __name__ == "__main__":
    sys.exit(main())
