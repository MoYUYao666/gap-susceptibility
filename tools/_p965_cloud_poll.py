# -*- coding: utf-8 -*-
r"""Poll the cloud setup log, and optionally start a remote command detached.

Started with `nohup ... &` inside an `exec_command`, the SSH channel stays open because the background
process inherits the pipe, so reading the channel blocks. Everything here therefore only reads files and
uses short, self-terminating commands.

    python tools/_p965_cloud_poll.py [--tail 25]
    python tools/_p965_cloud_poll.py --start "bash run_parity.sh" --log parity.log
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
USER = os.environ.get("P3SSH_USER", "root")
PASS = os.environ.get("P3SSH_PASS", "")
REMOTE = "/root/p3"


def connect() -> paramiko.SSHClient:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    return cli


def run(cli: paramiko.SSHClient, cmd: str, timeout: int = 60) -> str:
    _in, out, err = cli.exec_command(cmd, timeout=timeout)
    return (out.read().decode("utf-8", "replace") + err.read().decode("utf-8", "replace")).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="setup.log")
    ap.add_argument("--tail", type=int, default=25)
    ap.add_argument("--start", default="")
    ap.add_argument("--wait", type=int, default=0, help="seconds to wait before reading")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2

    cli = connect()
    if a.start:
        # setsid detaches fully, so the channel closes immediately
        cmd = (f"cd {REMOTE} && rm -f {a.log} && "
               f"setsid nohup bash -c {chr(39)}{a.start}{chr(39)} > {a.log} 2>&1 < /dev/null & "
               f"sleep 2; echo started")
        print("  " + run(cli, cmd))
    if a.wait:
        print(f"  waiting {a.wait} s")
        time.sleep(a.wait)
    print(f"  --- {a.log} (tail {a.tail}) ---")
    print(run(cli, f"cd {REMOTE} && tail -{a.tail} {a.log} 2>/dev/null || echo 'no log yet'", timeout=120))
    print("  --- processes ---")
    print(run(cli, "ps -eo pid,etime,pcpu,pmem,args --sort=-pcpu | grep -E 'install|python|pip' | "
                   "grep -v grep | head -6"))
    print("  --- disk / gpu ---")
    print(run(cli, "df -h / /root/autodl-tmp | tail -2; du -sh /root/autodl-tmp/hf 2>/dev/null; "
                   "nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
