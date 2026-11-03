# -*- coding: utf-8 -*-
r"""Run the 10 missing pre-registered arms with the correct tag names.

`strict_freeze_control.py` accepts only `text_only`, `both`, `vision_only` (the CONFIGS keys); my first queue used
`text` / `vision`, which raised `KeyError`. The five `both` arms succeeded. This launches the remaining
text_only x 5 seeds and vision_only x 5 seeds at 3-way parallelism.
"""
import io
import os

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westd.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "21492"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REMOTE = "/root/autodl-tmp/work"

DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg
: > logs/queue_fix.txt
for tag in text_only vision_only; do
  for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model models/clip-vit-base-patch32 --out-dir outputs/c_prereg --name clip_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/f_${tag}_${seed}.log 2>&1" >> logs/queue_fix.txt
  done
done
start=$(date +%s)
cat logs/queue_fix.txt | xargs -P 3 -I{} bash -c '{}'
end=$(date +%s)
echo "FIX_BATCH_DONE seconds=$((end-start)) arms=$(wc -l < logs/queue_fix.txt) results=$(find outputs/c_prereg -name results.json | wc -l)" > logs/FIX_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "_driver_fix.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_fix.sh")
sftp.close()

stdin, stdout, stderr = c.exec_command(
    "cd %s && sed -i 's/\\r$//' c_driver_fix.sh && chmod +x c_driver_fix.sh && "
    "(setsid nohup bash c_driver_fix.sh > logs/c_driver_fix.log 2>&1 < /dev/null &) ; sleep 3; "
    "echo started" % REMOTE, timeout=120)
print(stdout.read().decode("utf-8", "replace").strip())

stdin, stdout, stderr = c.exec_command(
    "sleep 60; cd %s; echo queue=$(wc -l < logs/queue_fix.txt); echo procs=$(ps aux | grep -c '[s]trict_freeze'); "
    "nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
    "echo results=$(find outputs/c_prereg -name results.json | wc -l); "
    "grep -h Traceback logs/f_*.log 2>/dev/null | head -2" % REMOTE, timeout=300)
print(stdout.read().decode("utf-8", "replace")[-1500:])
c.close()
