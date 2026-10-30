# -*- coding: utf-8 -*-
r"""One-shot status of the 2026-10-17 evening host: three downloads, disk, GPU, and running jobs.

Kept as a file because inline commands with nested quoting kept getting mangled by the local shell.

    python tools/_p1149_host_status.py
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

COMMANDS = [
    ("flickr", "tail -1 /root/p3/flickr_dl.log 2>/dev/null | tr -d '\\r'"),
    ("qwen2b", "tail -1 /root/p3/qwen2b_dl.log 2>/dev/null | tr -d '\\r'"),
    ("llava", "tail -1 /root/p3/llava_dl.log 2>/dev/null | tr -d '\\r'"),
    ("sizes", "du -sh /root/p3/data/flickr /root/autodl-tmp/hf/hub/models--Qwen--Qwen2-VL-2B-Instruct "
              "/root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf 2>/dev/null"),
    ("disk", "df -h /root/autodl-tmp | tail -1"),
    ("gpu", "nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader"),
    ("fetchers", "pgrep -c -f _p1101_parallel_fetch_any || echo 0"),
    ("shards", "ls /root/autodl-tmp/hf/hub/models--Qwen--Qwen2-VL-2B-Instruct/snapshots/main/*.safetensors "
               "2>/dev/null | wc -l"),
]


def main() -> int:
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    for name, cmd in COMMANDS:
        _i, o, e = cli.exec_command(cmd, timeout=120)
        out = (o.read() + e.read()).decode("utf-8", "replace").strip()
        print(f"  {name:<10} {out}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
