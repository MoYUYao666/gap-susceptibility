# -*- coding: utf-8 -*-
r"""Free space on the cloud host with a short remote command, because the disk is too full to upload.

SFTP writes fail on a filesystem with 200 KB free, so the cleanup cannot be delivered as a script file; it
is issued as a few simple commands instead. They delete only generated artefacts: the per-epoch checkpoints
(each finished arm already has its JSON record) and the pip wheel cache.

    python tools/_p1015_free_disk_inline.py [--apply]
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

STEPS = [
    ("before", "df -h / | tail -1"),
    ("delete checkpoints", "rm -f /root/p3/outputs/llava_bf16_sites/*.pt; find /root/p3 -name '*.pt' -delete; echo removed"),
    ("delete pip cache", "rm -rf /root/autodl-tmp/pipcache; echo removed"),
    ("delete logs of old attempts", "cd /root/p3 && rm -f resume2.log resume3.log sweep3.log tf32probe.log batchprobe.log smoke_bf16.log; echo removed"),
    ("after", "df -h / /root/autodl-tmp | tail -2"),
    ("p3 size", "du -sh /root/p3 2>/dev/null"),
    ("records", "ls /root/p3/outputs/llava_bf16_sites/ | tr '\\n' ' '"),
]


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
    for title, cmd in STEPS:
        _i, o, e = cli.exec_command(cmd, timeout=180)
        text = (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
        print(f"=== {title}")
        for line in text.splitlines()[:8]:
            print(f"    {line}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
