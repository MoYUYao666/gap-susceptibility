# -*- coding: utf-8 -*-
r"""SFTP helper for the cloud instance (paramiko). Password from P3_CLOUD_PW.

    python tools/_p1526_cloud_sftp.py --host H --port P put <local_file> <remote_path>
    python tools/_p1526_cloud_sftp.py --host H --port P get <remote_path> <local_path>
    python tools/_p1526_cloud_sftp.py --host H --port P mkdir <remote_dir>
"""
from __future__ import annotations

import argparse
import os
import stat

import paramiko


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--user", default="root")
    ap.add_argument("action", choices=["put", "get", "mkdir"])
    ap.add_argument("src")
    ap.add_argument("dst", nargs="?")
    a = ap.parse_args()
    pw = os.environ.get("P3_CLOUD_PW")
    if not pw:
        print("P3_CLOUD_PW not set")
        return 2
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(a.host, port=a.port, username=a.user, password=pw, timeout=30)
    sftp = c.open_sftp()
    if a.action == "mkdir":
        try:
            sftp.mkdir(a.src)
        except OSError as e:
            print("mkdir:", e)
    elif a.action == "put":
        sftp.put(a.src, a.dst)
        print("put", a.src, "->", a.dst, os.path.getsize(a.src), "bytes")
    else:
        sftp.get(a.src, a.dst)
        print("get", a.src, "->", a.dst, os.path.getsize(a.dst), "bytes")
    sftp.close()
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
