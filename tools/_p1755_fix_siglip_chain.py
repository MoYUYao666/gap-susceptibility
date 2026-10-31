# -*- coding: utf-8 -*-
r"""Fix the SigLIP blocker and chain its batch after the running B/16 batch.

Root cause (from the logs): the trainer patch works - `SiglipModel (model_type=siglip)` is selected and the weights
load - but `experiments/strict_freeze_control.py::layer_effective_ranks` indexes `ti["attention_mask"]`. SigLIP's
processor returns no attention mask (its tokenizer is non-padding), so the arm dies with `KeyError: 'attention_mask'`
before training starts. Fix: fall back to an all-ones mask of the same shape.

The driver waits for logs/B16_DONE so VRAM is never oversubscribed (2-way parallelism, 20 GB of 32.8 GB).
"""
import io
import os
import re

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westb.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "39308"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "/root/autodl-tmp/work"

# ---------------------------------------------------------------- patch the experiment script locally
P = os.path.join(REPO, "experiments", "strict_freeze_control.py")
t = io.open(P, encoding="utf-8").read()
OLD = 'ti["attention_mask"].to(DEVICE)'
NEW = 'ti.get("attention_mask", torch.ones_like(ti["input_ids"])).to(DEVICE)'
if OLD in t:
    t = t.replace(OLD, NEW)
    io.open(P, "w", encoding="utf-8", newline="\n").write(t)
    print("patched local strict_freeze_control.py: attention_mask fallback")
elif NEW in t:
    print("local script already carries the fallback")
else:
    raise SystemExit("attention_mask anchor not found - inspect the file before patching")

DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg_siglip
while [ ! -f logs/B16_DONE ]; do sleep 45; done
: > logs/queue_siglip2.txt
for tag in text_only both vision_only; do
  for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model models/siglip-base-patch16-224 --out-dir outputs/c_prereg_siglip --name siglip_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/s2_${tag}_${seed}.log 2>&1" >> logs/queue_siglip2.txt
  done
done
rm -f logs/SIGLIP_DONE
start=$(date +%s)
cat logs/queue_siglip2.txt | xargs -P 2 -I{} bash -c '{}'
end=$(date +%s)
echo "SIGLIP_DONE seconds=$((end-start)) results=$(find outputs/c_prereg_siglip -name results.json | wc -l)" > logs/SIGLIP_DONE
echo SIGLIP_CHAIN_DONE > logs/SIGLIP_CHAIN_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
sftp.put(P, REMOTE + "/experiments/strict_freeze_control.py")
tmp = os.path.join(REPO, "outputs", "_driver_siglip2.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_siglip2.sh")
sftp.close()
print("uploaded patched script + chained SigLIP driver")

stdin, stdout, stderr = c.exec_command(
    "cd %s && grep -c 'ones_like' experiments/strict_freeze_control.py && sed -i 's/\\r$//' c_driver_siglip2.sh && "
    "chmod +x c_driver_siglip2.sh && rm -rf outputs/c_prereg_siglip && "
    "(setsid nohup bash c_driver_siglip2.sh > logs/c_driver_siglip2.log 2>&1 < /dev/null &); sleep 2; "
    "echo chain=$(ps aux | grep -c '[c]_driver_siglip2'); "
    "echo b16=$(find outputs/c_prereg_b16 -name results.json 2>/dev/null | wc -l)" % REMOTE, timeout=180)
print(stdout.read().decode("utf-8", "replace").strip())
c.close()
