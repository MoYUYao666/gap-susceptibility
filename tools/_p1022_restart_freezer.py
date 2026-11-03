# -*- coding: utf-8 -*-
r"""Kill every running copy of the wait-and-freeze poller, then start the fixed one.

Two copies were running because `pkill -f _p1021_wait_and_freeze` did not match the process (its command
line is `bash _p1021_wait_and_freeze.sh`, and `-f` should have matched, but the pattern was also present in
its own `pkill` command line, which can make the result look ambiguous). This kills by pattern, verifies
nothing is left, and reports.

    python tools/_p1022_restart_freezer.py [--apply]
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

    def sh(cmd: str, timeout: int = 120) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    if not a.apply:
        print("  (dry run) running pollers:\n" + sh("pgrep -af wait_and_freeze || echo none"))
        cli.close()
        return 0

    print("  before:\n" + sh("pgrep -af wait_and_freeze | grep -v pgrep || echo none"))
    sh("pkill -9 -f wait_and_freeze.sh || true")
    time.sleep(3)
    left = sh("pgrep -af wait_and_freeze.sh | grep -v pgrep || echo none")
    print("  after kill:\n" + left)
    if "none" not in left:
        sh("for p in $(pgrep -f wait_and_freeze.sh); do kill -9 $p; done")
        time.sleep(2)
        print("  after second kill:\n" + sh("pgrep -af wait_and_freeze.sh | grep -v pgrep || echo none"))

    print("  starting the fixed poller")
    sh("cd /root/p3 && rm -f freeze2.log && setsid bash -c 'nohup bash _p1021_wait_and_freeze.sh "
       "> freeze2.log 2>&1' < /dev/null > /dev/null 2>&1 & disown; sleep 1")
    time.sleep(65)
    print("  freeze2.log:\n" + sh("tail -5 /root/p3/freeze2.log"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
