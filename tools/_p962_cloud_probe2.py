# -*- coding: utf-8 -*-
r"""Second look at the rented host: where python lives, and how much disk is really available.

The first probe found no `python` on PATH, which is unusual for a rented container, and only one 30 GB
filesystem, which matters because a 7B model needs about 15 GB. This looks for a conda installation and
for any additional mount before anything is downloaded.

    python tools/_p962_cloud_probe2.py
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
USER = os.environ.get("P3SSH_USER", "root")
PASS = os.environ.get("P3SSH_PASS", "")

COMMANDS = [
    ("mounts", "df -h | grep -v tmpfs"),
    ("conda dirs", "ls -d /root/miniconda3 /opt/conda /usr/local/miniconda3 /root/anaconda3 2>/dev/null; "
                   "ls /root/miniconda3/bin 2>/dev/null | head -20"),
    ("any python binary", "ls -l /usr/bin/python* /usr/local/bin/python* 2>/dev/null; "
                          "find / -maxdepth 4 -name 'python3*' -type f 2>/dev/null | head -10"),
    ("conda info", "/root/miniconda3/bin/conda info --envs 2>/dev/null || echo 'no conda'"),
    ("PATH", "echo $PATH"),
    ("data dirs", "ls -la /root/autodl-tmp /root/autodl-fs 2>/dev/null | head -20; "
                  "df -h /root/autodl-tmp /root/autodl-fs 2>/dev/null"),
    ("pip", "which pip pip3 2>/dev/null; /root/miniconda3/bin/pip --version 2>/dev/null || echo 'no pip'"),
    ("image hints", "cat /etc/issue 2>/dev/null | head -2; cat /root/.condarc 2>/dev/null; "
                    "nvidia-smi --query-gpu=driver_version --format=csv,noheader"),
]


def main() -> int:
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    for title, cmd in COMMANDS:
        _in, out, err = cli.exec_command(cmd, timeout=120)
        text = (out.read().decode("utf-8", "replace") + err.read().decode("utf-8", "replace")).strip()
        print(f"\n=== {title}")
        for line in text.splitlines()[:22]:
            print(f"    {line}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
