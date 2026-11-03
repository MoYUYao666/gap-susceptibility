# -*- coding: utf-8 -*-
r"""Chain the CLIP B/16 batch after the SigLIP batch so all remaining pre-registered arms run back-to-back.

The P2/P4 driver only queued the OpenCLIP arms: its weight check for `clip-vit-base-patch16` ran before
`pytorch_model.bin` was fully in place, so the B/16 block was skipped (the file is there now). Rather than restart the
running batch, B/16 waits for `logs/SIGLIP_DONE` and then runs its 15 arms. Every batch keeps the same 3-way
parallelism and the same protocol, so VRAM stays inside the measured ceiling.
"""
import io
import os

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westb.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "39308"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "/root/autodl-tmp/work"

DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg_b16
while [ ! -f logs/SIGLIP_DONE ]; do sleep 60; done
: > logs/queue_b16.txt
for tag in text_only both vision_only; do
  for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model models/clip-vit-base-patch16 --out-dir outputs/c_prereg_b16 --name b16_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/b16_${tag}_${seed}.log 2>&1" >> logs/queue_b16.txt
  done
done
start=$(date +%s)
cat logs/queue_b16.txt | xargs -P 3 -I{} bash -c '{}'
end=$(date +%s)
echo "B16_DONE seconds=$((end-start)) results=$(find outputs/c_prereg_b16 -name results.json | wc -l)" > logs/B16_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(REPO, "outputs", "_driver_b16_chain.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_b16_chain.sh")
sftp.close()
stdin, stdout, stderr = c.exec_command(
    "cd %s && sed -i 's/\\r$//' c_driver_b16_chain.sh && chmod +x c_driver_b16_chain.sh && "
    "(setsid nohup bash c_driver_b16_chain.sh > logs/c_driver_b16_chain.log 2>&1 < /dev/null &); sleep 2; "
    "echo b16_chain=$(ps aux | grep -c '[c]_driver_b16_chain'); "
    "echo p24_res=$(find outputs/c_prereg_openclip -name results.json 2>/dev/null | wc -l)" % REMOTE, timeout=180)
print(stdout.read().decode("utf-8", "replace").strip())
c.close()
