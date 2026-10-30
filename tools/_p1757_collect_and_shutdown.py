# -*- coding: utf-8 -*-
r"""Retrieve the finished pre-registered results and shut the instance down.

State on the instance: OpenCLIP (P2) 15/15 and CLIP B/16 (P4) 15/15 are complete; SigLIP (P3) produced 0 because the
SigLIP text tower caps at 64 positions while the pipeline pads to CLIP's 77 - an architecture mismatch that needs a
tokenizer-length change, not a data or weight problem. P3 is therefore deferred and recorded as such.

Order per the cloud rule: confirm processes gone -> retrieve every results.json -> verify size -> shutdown -> port probe.
"""
import io
import json
import os
import socket

import paramiko

HOST = "connect.westb.seetacloud.com"
PORT = 39308
USER = "root"
PWD = os.environ["CLOUD_PASS"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "/root/autodl-tmp/work"
SETS = [("openclip", "outputs/c_prereg_openclip"), ("b16", "outputs/c_prereg_b16"),
        ("siglip", "outputs/c_prereg_siglip")]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)

stdin, stdout, stderr = c.exec_command("ps aux | grep -c '[s]trict_freeze_control'", timeout=60)
print("running processes:", stdout.read().decode().strip())

sftp = c.open_sftp()
total = 0
for name, remote_dir in SETS:
    local_dir = os.path.join(REPO, "outputs", "paperA_c_prereg_" + name)
    os.makedirs(local_dir, exist_ok=True)
    stdin, stdout, stderr = c.exec_command("find %s/%s -name results.json" % (REMOTE, remote_dir), timeout=60)
    paths = [p for p in stdout.read().decode().split() if p.strip()]
    ok = 0
    for rp in paths:
        rel = rp.replace(REMOTE + "/" + remote_dir + "/", "").replace("/", "__")
        lp = os.path.join(local_dir, rel)
        try:
            sftp.get(rp, lp)
            if os.path.getsize(lp) > 1024:
                ok += 1
        except Exception as e:
            print("  download failed:", rp, e)
    print("%-9s downloaded %d/%d files" % (name, ok, len(paths)))
    total += ok
sftp.close()
print("total results retrieved:", total)

stdin, stdout, stderr = c.exec_command(
    "sync; (shutdown -h now || poweroff || /usr/bin/shutdown -h now) > /dev/null 2>&1 & sleep 2; echo shutdown-requested",
    timeout=120)
print(stdout.read().decode("utf-8", "replace").strip())
c.close()

try:
    s = socket.create_connection((HOST, PORT), timeout=8)
    s.close()
    print("port still open: instance NOT down yet")
except Exception:
    print("port 39308 closed: instance is down")
