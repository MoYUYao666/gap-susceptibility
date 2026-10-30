# -*- coding: utf-8 -*-
r"""Inspect the cloud run's log and process state when the signals disagree.

The monitor showed both a mid-sweep run name (`text_only_s123`) and a completion marker, with the GPU idle
at 1 MiB. One of those readings is wrong and the difference matters: if the sweep really finished, the
records are complete; if it died, they are not.

    python tools/_p1002_diagnose_run.py
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

CHECKS = [
    ("log tail", "tail -30 /root/p3/final_sweep.log"),
    ("log size and time", "ls -la --time-style=+%H:%M:%S /root/p3/final_sweep.log; date +%H:%M:%S"),
    ("processes", "pgrep -af '_p820_llava_sites|_p999_cloud_final' | head -4 || echo none"),
    ("gpu", "nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader"),
    ("records", "ls -la /root/p3/outputs/llava_bf16_sites/*.json"),
    ("record count with arm", "for f in /root/p3/outputs/llava_bf16_sites/*.json; do "
                              "python3 -c \"import json,sys;d=json.load(open(sys.argv[1]));"
                              "print(d.get('arm'),d.get('seed'),d.get('samples'),d.get('epochs'))\" "
                              "\"$f\" 2>/dev/null; done | sort | uniq -c"),
    ("done markers", "grep -n 'BF16_SWEEP_DONE' /root/p3/final_sweep.log"),
    ("all run headers", "grep -nE '^(frozen|text_only|vision_only|both)_s[0-9]+$' /root/p3/final_sweep.log"),
    ("summary lines", "grep -nE 'summary by arm|wrote ' /root/p3/final_sweep.log | tail -6"),
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
        for line in text.splitlines()[:32]:
            print(f"    {line}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
