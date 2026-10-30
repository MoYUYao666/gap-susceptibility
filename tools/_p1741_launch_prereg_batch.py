# -*- coding: utf-8 -*-
r"""Launch the pre-registered prediction batch (workstream C) on the instance.

Sequence: 1-epoch smoke -> if it produces a results.json, start the detached batch:
  backbones  : CLIP B/32 (P1) and SigLIP B/16 (P3, the reversal case)
  sites      : text / both / vision        (strict freezing)
  seeds      : 42, 123, 456, 789, 1012     (1012 is NOT one of the six archived seeds)
  protocol   : rank 8, alpha = 2*rank, 10 epochs, 5000 samples, batch 128, --dg-star
Parallelism: 3 concurrent arms (measured VRAM after the smoke; 32 GB card).
A GPU sampler and a DONE marker make the batch self-reporting.
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
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
PY=/root/miniconda3/bin/python
CLIP=$(ls -d /root/autodl-tmp/hf/hub/models--openai--clip-vit-base-patch32/snapshots/* | head -1)
SIG=$(ls -d /root/autodl-tmp/hf/hub/models--google--siglip-base-patch16-224/snapshots/* | head -1)
mkdir -p logs outputs/c_prereg
: > logs/queue.txt
for spec in "clip:$CLIP" "siglip:$SIG"; do
  tag=${spec%%:*}; model=${spec#*:}
  for site in text both vision; do
    for seed in 42 123 456 789 1012; do
      echo "$PY experiments/strict_freeze_control.py --model $model --out-dir outputs/c_prereg --name ${tag}_ --rank 8 --alpha-mult 2 --tags $site --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/c_${tag}_${site}_${seed}.log 2>&1" >> logs/queue.txt
    done
  done
done
ppid=$$
( nvidia-smi --query-gpu=memory.used --format=csv,noheader -l 60 > logs/gpu_c.log 2>&1 & echo $! > logs/gpu_c.pid )
start=$(date +%s)
cat logs/queue.txt | xargs -P 3 -I{} bash -c '{}'
end=$(date +%s)
kill "$(cat logs/gpu_c.pid)" 2>/dev/null
echo "C_BATCH_DONE seconds=$((end-start))" > logs/C_DONE
"""

SMOKE = (
    "cd %s && export HF_HOME=/root/autodl-tmp/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 && "
    "CLIP=$(ls -d /root/autodl-tmp/hf/hub/models--openai--clip-vit-base-patch32/snapshots/* | head -1) && "
    "/root/miniconda3/bin/python experiments/strict_freeze_control.py --model \"$CLIP\" --smoke "
    "--out-dir outputs/_smoke --name smoke_ --tags both --seeds 42 --epochs 1 --max-samples 200 "
    "--batch-size 32 --skip-frozen --dg-star 2>&1 | tail -6 && echo '--- results ---' && "
    "ls outputs/_smoke 2>/dev/null | head -5 && du -sh outputs/_smoke 2>/dev/null"
) % REMOTE

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)

local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "_c_driver.sh")
io.open(local, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp = c.open_sftp()
sftp.put(local, REMOTE + "/c_driver.sh")
sftp.close()

stdin, stdout, stderr = c.exec_command("sed -i 's/\\r$//' %s/c_driver.sh && chmod +x %s/c_driver.sh && echo ok" % (REMOTE, REMOTE), timeout=120)
print("upload driver:", stdout.read().decode("utf-8", "replace").strip())

print("\n=== smoke run (1 epoch, 200 samples) ===")
stdin, stdout, stderr = c.exec_command(SMOKE, timeout=1500)
print(stdout.read().decode("utf-8", "replace")[-3000:])
err = stderr.read().decode("utf-8", "replace")
if err.strip():
    print("--- stderr ---", err[-1200:])

stdin, stdout, stderr = c.exec_command(
    "cd %s && ls outputs/_smoke/**/results.json 2>/dev/null | head -2" % REMOTE, timeout=120)
found = stdout.read().decode("utf-8", "replace").strip()
print("\nsmoke results.json:", found or "NONE")

if found:
    stdin, stdout, stderr = c.exec_command(
        "cd %s && setsid nohup bash c_driver.sh > logs/c_driver.log 2>&1 < /dev/null & sleep 8; "
        "echo started; cat logs/queue.txt | wc -l; ps aux | grep strict_freeze | grep -v grep | wc -l" % REMOTE,
        timeout=180)
    print("\n=== batch launched ===")
    print(stdout.read().decode("utf-8", "replace"))
else:
    print("\nsmoke did NOT produce results.json - batch NOT started (see stderr above)")
c.close()
