# -*- coding: utf-8 -*-
r"""Read the CURRENT run's log and process state.

`_p1002` reads `final_sweep.log`, which is the log of the first attempt (the one that hit the warm-up OOM).
The restart writes to `resume2.log`, so diagnosing from the old file reports a failure that has already been
fixed. This reads the live log and both logs' timestamps side by side.

    python tools/_p1005_current_run.py
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

CHECKS = [
    ("time", "date +%H:%M:%S"),
    ("logs", "ls -la --time-style=+%H:%M:%S /root/p3/*.log"),
    ("processes", "pgrep -af '_p820_llava_sites|_p1004_cloud_resume' | head -4 || echo none"),
    ("gpu", "nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader"),
    ("resume log tail", "tail -25 /root/p3/resume2.log 2>/dev/null || echo 'no resume2.log'"),
    ("resume errors", "grep -cE 'Traceback|OutOfMemory' /root/p3/resume2.log 2>/dev/null || true"),
    ("resume markers", "grep -nE 'BF16_SWEEP_DONE|skipping|^[a-z_]+_s[0-9]+$' /root/p3/resume2.log 2>/dev/null | tail -8"),
    ("records", "ls -la --time-style=+%H:%M:%S /root/p3/outputs/llava_bf16_sites/*.json 2>/dev/null"),
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
        for line in text.splitlines()[:26]:
            print(f"    {line}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
