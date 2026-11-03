# -*- coding: utf-8 -*-
r"""Run one command on the cloud instance over SSH (paramiko).

    python tools/_p1525_cloud_exec.py --host HOST --port PORT --user root --cmd "nvidia-smi"

The password is read from the environment variable P3_CLOUD_PW (not stored in the repository).
"""
from __future__ import annotations

import argparse
import os
import sys

import paramiko


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--user", default="root")
    ap.add_argument("--cmd", required=True)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--detach", action="store_true")
    a = ap.parse_args()
    pw = os.environ.get("P3_CLOUD_PW")
    if not pw:
        print("P3_CLOUD_PW not set")
        return 2
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(a.host, port=a.port, username=a.user, password=pw, timeout=30,
              banner_timeout=30, auth_timeout=30)
    if a.detach:
        tr = c.get_transport()
        ch = tr.open_session()
        ch.exec_command(a.cmd)
        ch.close()
        c.close()
        print("detached")
        return 0
    stdin, stdout, stderr = c.exec_command(a.cmd, timeout=a.timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    print(out)
    if err.strip():
        print("STDERR:", err[-2000:])
    c.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
