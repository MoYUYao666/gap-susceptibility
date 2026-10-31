# -*- coding: utf-8 -*-
r"""Tiny SSH/SFTP helper for the A3 cloud run (local side).

Credentials are read from a JSON file outside version control (default local_runs/cloud_creds.json) with the keys
host, port, user, password. Never commit that file.

Usage
  python tools/_p1803_ssh_runner.py exec "<command>" [--timeout 120]
  python tools/_p1803_ssh_runner.py put <local> <remote>
  python tools/_p1803_ssh_runner.py get <remote> <local>
"""
import argparse
import io
import json
import os
import sys

import paramiko

CREDS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_runs", "cloud_creds.json")


def connect():
    d = json.loads(io.open(CREDS, encoding="utf-8").read())
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=d["host"], port=int(d["port"]), username=d.get("user", "root"),
                   password=d["password"], timeout=30, banner_timeout=30, auth_timeout=30)
    return client


def exec_cmd(cmd, timeout=120):
    client = connect()
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        stdin.close()
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        code = stdout.channel.recv_exit_status()
        sys.stdout.write(out)
        if err.strip():
            sys.stderr.write("\n[stderr]\n" + err)
        return code
    finally:
        client.close()


def put(local, remote):
    client = connect()
    try:
        sftp = client.open_sftp()
        sftp.put(local, remote)
        print("uploaded %s -> %s" % (local, remote))
    finally:
        client.close()


def get(remote, local):
    client = connect()
    try:
        sftp = client.open_sftp()
        sftp.get(remote, local)
        print("downloaded %s -> %s" % (remote, local))
    finally:
        client.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["exec", "put", "get"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--timeout", type=int, default=120)
    ns = ap.parse_args()
    if ns.action == "exec":
        return exec_cmd(" ".join(ns.args), timeout=ns.timeout)
    if ns.action == "put":
        return put(ns.args[0], ns.args[1])
    return get(ns.args[0], ns.args[1])


if __name__ == "__main__":
    raise SystemExit(main())
