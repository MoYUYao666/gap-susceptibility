# -*- coding: utf-8 -*-
r"""Run one command on the cloud host detached, and report it has started.

Needed because a long remote command keeps the SSH channel open, so reading it blocks; the command is
launched under `setsid nohup` and its output goes to a log that `_p965_cloud_poll.py` reads.

    python tools/_p969_cloud_run.py --log fix.log --cmd "pip install torchvision==0.24.1 ..."
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
REMOTE = "/root/p3"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True)
    ap.add_argument("--log", default="run.log")
    ap.add_argument("--tail", type=int, default=0, help="seconds to wait, then show the log")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    # write the command to a file so quoting cannot be mangled on the way in
    sftp = cli.open_sftp()
    with sftp.open(f"{REMOTE}/cmd.sh", "w") as fh:
        fh.write("#!/usr/bin/env bash\nset -uo pipefail\n" + a.cmd + "\n")
    sftp.close()

    launch = (f"cd {REMOTE} && chmod +x cmd.sh && rm -f {a.log} && "
              f"setsid nohup bash cmd.sh > {a.log} 2>&1 < /dev/null & sleep 2; echo launched")
    _i, o, e = cli.exec_command(launch, timeout=60)
    print("  " + (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip())

    if a.tail:
        print(f"  waiting {a.tail} s")
        time.sleep(a.tail)
        _i, o, _e = cli.exec_command(f"cd {REMOTE} && tail -20 {a.log}", timeout=120)
        print(o.read().decode("utf-8", "replace"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
