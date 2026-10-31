# -*- coding: utf-8 -*-
r"""Upload a local shell script to the cloud host and run it detached.

Writing the script locally avoids every quoting problem: PowerShell never sees the remote command's
contents, and the file arrives byte for byte.

    python tools/_p971_cloud_push_run.py --script tools/_p970_fix_torchvision.sh --log fix.log --wait 120
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
    ap.add_argument("--script", required=True)
    ap.add_argument("--log", default="")
    ap.add_argument("--wait", type=int, default=0)
    ap.add_argument("--tail", type=int, default=25)
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    local = os.path.abspath(a.script)
    name = os.path.basename(local)
    log = a.log or (os.path.splitext(name)[0] + ".log")

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    sftp = cli.open_sftp()
    remote = f"{REMOTE}/{name}"
    sftp.put(local, remote)
    sftp.close()
    print(f"  uploaded {name} ({os.path.getsize(local)} bytes)")

    # Detach properly: `setsid` puts the process in its own session, stdin comes from /dev/null and both
    # streams go to the log file, so the SSH channel is not held open by an inherited pipe. Without this
    # the read below blocks until the remote job finishes (paramiko PipeTimeout), which is how this failed
    # on the first attempt. Nothing is echoed in the same line either, for the same reason.
    launch = (f"cd {REMOTE} && chmod +x {name} && rm -f {log} && "
              f"setsid bash -c 'nohup bash {name} > {log} 2>&1' < /dev/null > /dev/null 2>&1 & "
              f"disown; sleep 1")
    cli.exec_command(launch, timeout=30)
    time.sleep(3)
    _i, o, e = cli.exec_command(f"cd {REMOTE} && (test -f {log} && echo 'log created' || echo 'no log'); "
                                f"pgrep -af 'bash {name}' | head -2", timeout=60)
    print("  " + (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip())

    if a.wait:
        print(f"  waiting {a.wait} s")
        time.sleep(a.wait)
    _i, o, e = cli.exec_command(f"cd {REMOTE} && tail -{a.tail} {log} 2>/dev/null || echo 'no log'",
                                timeout=120)
    print(f"  --- {log} ---")
    print(o.read().decode("utf-8", "replace"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
