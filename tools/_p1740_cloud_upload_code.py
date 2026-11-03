# -*- coding: utf-8 -*-
r"""Upload the Paper A training code to the instance and probe the CLI.

This instance's data disk is a copy of the P3 machine, so it has the models and the flickr30k dataset but not the
Paper A work tree. Upload only what the runner needs (experiments/, src/, configs/, requirements), show the remote
layout, then ask the training script for its --help so the exact flags are known before launching.
"""
import io
import os
import stat
import sys

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westd.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "21492"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "/root/autodl-tmp/work"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()


def mkdirs(path):
    parts = path.strip("/").split("/")
    cur = ""
    for p in parts:
        cur += "/" + p
        try:
            sftp.stat(cur)
        except IOError:
            sftp.mkdir(cur)


mkdirs(REMOTE)
mkdirs(REMOTE + "/experiments")
mkdirs(REMOTE + "/src")

sent = 0
bytes_sent = 0
for rel in ("experiments", "src"):
    root = os.path.join(REPO, rel)
    if not os.path.isdir(root):
        continue
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.endswith((".py", ".json", ".yaml", ".yml", ".sh")):
                continue
            local = os.path.join(dirpath, f)
            relp = os.path.relpath(local, REPO).replace("\\", "/")
            remote = REMOTE + "/" + relp
            mkdirs(os.path.dirname(remote))
            sftp.put(local, remote)
            sent += 1
            bytes_sent += os.path.getsize(local)

print("uploaded files:", sent, "| MB:", round(bytes_sent / 1048576, 2))
sftp.close()

cmd = (
    "cd %s && echo '== layout =='; ls | head; echo '== exp =='; ls experiments | head -6; "
    "echo '== python deps =='; /root/miniconda3/bin/python -c 'import torch,transformers,peft;"
    "print(torch.__version__, transformers.__version__, peft.__version__)' 2>&1 | tail -2; "
    "echo '== clip model =='; ls /root/autodl-tmp/hf/hub/models--openai--clip-vit-base-patch32/snapshots 2>/dev/null | head -3; "
    "echo '== flickr =='; ls /root/autodl-tmp/hf/hub/datasets--nlphuji--flickr30k/snapshots 2>/dev/null | head -2; "
    "echo '== help =='; /root/miniconda3/bin/python experiments/strict_freeze_control.py --help 2>&1 | head -45"
) % REMOTE

stdin, stdout, stderr = c.exec_command(cmd, timeout=600)
out = stdout.read().decode("utf-8", "replace")
err = stderr.read().decode("utf-8", "replace")
print(out)
if err.strip():
    print("--- stderr ---")
    print(err[-2000:])
c.close()
