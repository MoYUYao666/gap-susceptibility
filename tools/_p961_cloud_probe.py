# -*- coding: utf-8 -*-
r"""Probe the rented GPU host over SSH: hardware, disk, python, and what is already installed.

Credentials are taken from the environment (`P3SSH_HOST`, `P3SSH_PORT`, `P3SSH_PASS`) so they are never
written to a file or a repository. `P3SSH_USER` defaults to root.

    python tools/_p961_cloud_probe.py
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
    ("hostname / date", "hostname; date; uname -a"),
    ("GPU", "nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader"),
    ("CUDA toolkit", "nvcc --version 2>/dev/null | tail -2 || echo 'no nvcc (fine, wheels carry their own)"),
    ("GPU processes", "nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader"),
    ("CPU / RAM", "nproc; free -g | head -2"),
    ("disk", "df -h / /root 2>/dev/null | head -4"),
    ("python", "which python python3; python -V 2>&1; python3 -V 2>&1"),
    ("conda envs", "ls -d /root/miniconda3/envs/* 2>/dev/null; ls -d /root/autodl-tmp 2>/dev/null"),
    ("torch/transformers already?", "python -c \"import torch,transformers;print('torch',torch.__version__,'cuda',torch.version.cuda,'| transformers',transformers.__version__)\" 2>&1 | tail -2"),
    ("HF cache present?", "du -sh ~/.cache/huggingface 2>/dev/null || echo 'no HF cache'"),
    ("network to mirrors", "curl -sS -m 8 -o /dev/null -w 'hf-mirror %{http_code}\\n' https://hf-mirror.com 2>&1; curl -sS -m 8 -o /dev/null -w 'pypi %{http_code}\\n' https://pypi.org/simple/ 2>&1"),
    ("existing work dirs", "ls -la /root | head -20"),
]


def main() -> int:
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set; nothing to do")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    print(f"  connected to {USER}@{HOST}:{PORT}")
    for title, cmd in COMMANDS:
        _in, out, err = cli.exec_command(cmd, timeout=60)
        text = out.read().decode("utf-8", "replace").strip()
        errtext = err.read().decode("utf-8", "replace").strip()
        print(f"\n=== {title}")
        for line in (text or errtext).splitlines():
            print(f"    {line}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
