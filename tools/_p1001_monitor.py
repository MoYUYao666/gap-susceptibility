# -*- coding: utf-8 -*-
r"""One monitoring sweep of the cloud run, printed as a short status block.

Written as a file rather than an inline command because PowerShell mangles the quoting of `grep -E "A|B"`
style arguments before Python sees them, which has now broken several checks in this session.

    python tools/_p1001_monitor.py
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
OUT = "/root/p3/outputs/llava_bf16_sites"
LOG = "/root/p3/final_sweep.log"

CHECKS = [
    ("files", f"ls {OUT}/ | tr '\\n' ' '"),
    ("progress", f"cat {OUT}/train_progress.json 2>/dev/null | head -9"),
    ("runs seen", "grep -E '^(frozen|text_only|vision_only|both)_s[0-9]+$' " + LOG + " | tail -4"),
    ("records with arm", f"grep -l '\"arm\"' {OUT}/*.json 2>/dev/null | wc -l"),
    ("errors", "grep -cE 'Traceback|CUDA out of memory' " + LOG + " || true"),
    ("losses", "grep -E 's/step' " + LOG + " | tail -3"),
    ("gpu/disk", "nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader; "
                 "df -h /root/autodl-tmp | tail -1"),
    ("done marker", "grep -c BF16_SWEEP_DONE " + LOG + " || true"),
]


def main() -> int:
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    for title, cmd in CHECKS:
        _i, o, e = cli.exec_command(cmd, timeout=180)
        text = (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
        print(f"=== {title}")
        for line in text.splitlines()[:10]:
            print(f"    {line}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
