# -*- coding: utf-8 -*-
r"""Check how the rented host can be shut down, without shutting it down.

Three routes are possible on AutoDL: an in-container `shutdown -h now`, the AutoDL web console, or the
host's API with the instance token. This only reports which are present, and which user commands exist,
so the final step can use the one that works.

    python tools/_p983_cloud_shutdown_probe.py
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

CMD = r"""
echo "=== whoami / privilege ==="; id -u; whoami
echo "=== shutdown binaries ==="
for c in shutdown poweroff halt autodl; do command -v $c || echo "  no $c"; done
echo "=== shutdown help ==="; shutdown --help 2>&1 | head -5
echo "=== systemd present? ==="; [ -d /run/systemd/system ] && echo "systemd active" || echo "no systemd (container)"
echo "=== instance hint files ==="
ls -la /root/autodl-tmp/.autodl 2>/dev/null; cat /root/autodl-tmp/.autodl/* 2>/dev/null | head -5
echo "=== sweep still alive? ==="
pgrep -af "_p820_llava_sites" | head -2 || echo "  no sweep process"
tail -3 /root/p3/bf16_sweep2.log
"""


def main() -> int:
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    _i, o, e = cli.exec_command(CMD, timeout=120)
    print((o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip())
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
