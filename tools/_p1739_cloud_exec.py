# -*- coding: utf-8 -*-
r"""Run one shell command on the AutoDL instance over SSH (password auth via paramiko).

Usage: python tools/_p1739_cloud_exec.py "<command>"
Host/port/user/password come from the environment so nothing secret lands in the repo:
  CLOUD_HOST, CLOUD_PORT, CLOUD_USER, CLOUD_PASS
"""
import os
import sys

import paramiko

host = os.environ.get("CLOUD_HOST", "connect.westd.seetacloud.com")
port = int(os.environ.get("CLOUD_PORT", "21492"))
user = os.environ.get("CLOUD_USER", "root")
pwd = os.environ["CLOUD_PASS"]
cmd = sys.argv[1] if len(sys.argv) > 1 else "hostname; nvidia-smi -L"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(host, port=port, username=user, password=pwd, timeout=30, banner_timeout=30, auth_timeout=30)
stdin, stdout, stderr = c.exec_command(cmd, timeout=1800)
out = stdout.read().decode("utf-8", "replace")
err = stderr.read().decode("utf-8", "replace")
rc = stdout.channel.recv_exit_status()
print(out)
if err.strip():
    print("--- stderr ---")
    print(err[-3000:])
print("--- rc:", rc)
c.close()
