# -*- coding: utf-8 -*-
r"""Ask the cloud host one thing at a time, without inline quoting games.

PowerShell folds the quoting of an inline `python -c "..."` before Python ever sees it, which has broken
several calls in this session. This script keeps the remote commands in a list of plain strings and writes
their output verbatim.

    python tools/_p967_cloud_ask.py
    python tools/_p967_cloud_ask.py --cmd "nvidia-smi -L"
"""
from __future__ import annotations

import argparse
import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

DEFAULT = [
    ("setup done?", "grep -c SETUP_DONE /root/p3/setup.log || true"),
    ("setup tail", "tail -4 /root/p3/setup.log"),
    ("peft version", r""" /root/miniconda3/bin/python - <<'EOF'
import importlib
for m in ("peft", "torch", "transformers", "bitsandbytes", "accelerate"):
    try:
        print(m, getattr(importlib.import_module(m), "__version__", "?"))
    except Exception as exc:
        print(m, "ERR", exc)
EOF"""),
    ("hf cache", "du -sh /root/autodl-tmp/hf; ls /root/autodl-tmp/hf/hub"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", action="append", default=[])
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    todo = [("cmd", c) for c in a.cmd] or DEFAULT
    for title, cmd in todo:
        _i, o, e = cli.exec_command(cmd, timeout=120)
        text = (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
        print(f"=== {title}")
        for line in text.splitlines()[:20]:
            print(f"    {line}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
