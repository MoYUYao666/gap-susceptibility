# -*- coding: utf-8 -*-
r"""Upload the sweep to the cloud host and prove the remote copy parses before anything runs.

A local parse is not enough: on 2026-10-16 an earlier upload raced a file that was momentarily broken and
the remote run died with IndentationError while the local check said OK. This uploads, parses with the
host's own interpreter, and only then returns success.

    python tools/_p998_cloud_sync_sweep.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWEEP = os.path.join(REPO, "tools", "_p820_llava_sites.py")
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
REMOTE = "/root/p3/tools/_p820_llava_sites.py"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    if not a.apply:
        print("  (dry run)")
        return 0

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    sftp = cli.open_sftp()
    sftp.put(SWEEP, REMOTE)
    st = sftp.stat(REMOTE)
    sftp.close()
    print(f"  uploaded {os.path.getsize(SWEEP)} bytes; remote size {st.st_size}")

    check = ("/root/miniconda3/bin/python -c \"import ast,io;"
             "ast.parse(io.open('" + REMOTE + "',encoding='utf-8').read());"
             "s=io.open('" + REMOTE + "',encoding='utf-8').read();"
             "print('REMOTE_PARSE_OK', '--tf32' in s, '--eval-batch' in s, '--precision' in s)\"")
    _i, o, e = cli.exec_command(check, timeout=120)
    out = (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
    print("  " + out)
    ok = "REMOTE_PARSE_OK True True True" in out
    cli.close()
    if not ok:
        print("  the remote copy is not usable; nothing should be run against it")
        return 1
    print("  the remote sweep is the patched one and parses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
