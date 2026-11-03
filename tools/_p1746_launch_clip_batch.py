# -*- coding: utf-8 -*-
r"""Launch the CLIP-only half of the pre-registered batch.

The full batch crashed on the SigLIP arms (`KeyError: 'vision'`): the training script maps CLIP's `vision_model` /
`text_model` block names, while transformers exposes SigLIP under different attribute names. The CLIP arms are proven
by the smoke run, so start those 15 now (3 sites x 5 seeds) and leave SigLIP for a block-map adaptation.
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
: > logs/queue_clip.txt
for site in text both vision; do
  for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model models/clip-vit-base-patch32 --out-dir outputs/c_prereg --name clip_ --rank 8 --alpha-mult 2 --tags $site --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/c_clip_${site}_${seed}.log 2>&1" >> logs/queue_clip.txt
  done
done
( nvidia-smi --query-gpu=memory.used --format=csv,noheader -l 60 > logs/gpu_clip.log 2>&1 & echo $! > logs/gpu_clip.pid )
start=$(date +%s)
cat logs/queue_clip.txt | xargs -P 3 -I{} bash -c '{}'
end=$(date +%s)
kill "$(cat logs/gpu_clip.pid)" 2>/dev/null
echo "CLIP_BATCH_DONE seconds=$((end-start)) arms=$(wc -l < logs/queue_clip.txt) results=$(find outputs/c_prereg -name results.json | wc -l)" > logs/CLIP_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "_driver_clip.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_clip.sh")
sftp.close()

stdin, stdout, stderr = c.exec_command(
    "cd %s && sed -i 's/\\r$//' c_driver_clip.sh && chmod +x c_driver_clip.sh && "
    "setsid nohup bash c_driver_clip.sh > logs/c_driver_clip.log 2>&1 < /dev/null & sleep 40; "
    "cd %s; echo '== queue =='; wc -l < logs/queue_clip.txt; echo '== procs =='; ps aux | grep -c '[s]trict_freeze'; "
    "echo '== gpu =='; nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
    "echo '== log tails =='; for f in $(ls -t logs/c_clip_*.log | head -2); do echo \"--- $f\"; tail -2 \"$f\"; done"
    % (REMOTE, REMOTE), timeout=300)
print(stdout.read().decode("utf-8", "replace")[-2500:])
c.close()
