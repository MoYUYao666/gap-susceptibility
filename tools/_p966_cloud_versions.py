# -*- coding: utf-8 -*-
r"""Read the cloud setup's version self-check and completion marker.

    python tools/_p966_cloud_versions.py
"""
from __future__ import annotations

import os
import re
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")


def main() -> int:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 90) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    log = sh("cat /root/p3/setup.log")
    print("=== version self-check ===")
    m = re.search(r"=== version self-check ===(.*?)(?==== |\Z)", log, re.S)
    print(m.group(1).strip() if m else "(not reached yet)")
    print()
    print("=== pip install results ===")
    for line in log.splitlines():
        if line.startswith("Successfully installed") or "ERROR" in line or "error:" in line:
            print("   ", line[:160])
    print()
    print("=== completion ===")
    print("   SETUP_DONE present:", "SETUP_DONE" in log)
    tail = [l for l in log.splitlines() if l.strip()][-6:]
    print("   last lines:")
    for line in tail:
        print("     ", line[:150])
    print()
    print("=== host state ===")
    print(sh("df -h / /root/autodl-tmp | tail -2; du -sh /root/autodl-tmp/hf; "
             "ls /root/autodl-tmp/hf/hub 2>/dev/null"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
