# -*- coding: utf-8 -*-
r"""Upload the two patched source files and run the SigLIP (P3) arms on the fresh instance.

The instance's data disk is a copy of the earlier one, so the corpus, all four checkpoints and the helper scripts are
already there; only `src/trainer.py` and `src/dataset.py` predate the backbone-aware sequence-length fix. This uploads
just those two files, writes a one-arm-at-a-time driver (B/16's `both` arms needed 20 GB, so parallelism 1 is the only
safe setting) and starts it detached.
"""
import io
import os

import paramiko

HOST = "connect.westd.seetacloud.com"
PORT = 32190
USER = "root"
PWD = os.environ["CLOUD_PASS"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "/root/autodl-tmp/work"

DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg_siglip
: > logs/queue_p3.txt
for tag in text_only both vision_only; do
  for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model models/siglip-base-patch16-224 --out-dir outputs/c_prereg_siglip --name siglip_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/p3_${tag}_${seed}.log 2>&1" >> logs/queue_p3.txt
  done
done
start=$(date +%s)
cat logs/queue_p3.txt | xargs -P 1 -I{} bash -c '{}'
end=$(date +%s)
echo "P3_DONE seconds=$((end-start)) results=$(find outputs/c_prereg_siglip -name results.json | wc -l)" > logs/P3_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
for rel in ("src/trainer.py", "src/dataset.py"):
    sftp.put(os.path.join(REPO, rel), REMOTE + "/" + rel)
tmp = os.path.join(REPO, "outputs", "_driver_p3.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_p3.sh")
sftp.close()
print("uploaded trainer.py, dataset.py and the P3 driver")

stdin, stdout, stderr = c.exec_command(
    "cd %s && grep -c PEFT_MAX_SEQ_LEN src/trainer.py src/dataset.py && chmod +x c_driver_p3.sh && "
    "rm -rf outputs/c_prereg_siglip && (setsid nohup bash c_driver_p3.sh > logs/p3_driver.log 2>&1 < /dev/null &); "
    "sleep 75; echo queue=$(wc -l < logs/queue_p3.txt 2>/dev/null); "
    "echo procs=$(ps aux | grep -c '[s]trict_freeze_control'); "
    "nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
    "grep -h -m1 'text sequence length' logs/p3_*.log 2>/dev/null | head -2; "
    "grep -h -m1 'Traceback\\|ValueError' logs/p3_*.log 2>/dev/null | head -2" % REMOTE, timeout=420)
print(stdout.read().decode("utf-8", "replace")[-1500:])
c.close()
