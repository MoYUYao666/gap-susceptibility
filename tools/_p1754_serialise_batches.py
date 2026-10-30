# -*- coding: utf-8 -*-
r"""Take control of the instance: stop the overlapping batches and run the three remaining pre-registered sets strictly
one after another.

Why: an earlier chained SigLIP attempt crashed instantly and wrote SIGLIP_DONE, so the B/16 chain started while SigLIP
was actually running - three batches were competing for 32.8 GB (measured 9.2 GB/arm, ceiling 3 arms). This driver
serialises the batches, each with a fresh queue and its own completion marker.
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
mkdir -p logs
run_set () {  # $1 = model dir, $2 = out dir, $3 = name prefix, $4 = log prefix, $5 = done marker
  : > logs/queue_$4.txt
  for tag in text_only both vision_only; do
    for seed in 42 123 456 789 1012; do
      echo "$PY experiments/strict_freeze_control.py --model $1 --out-dir $2 --name $3 --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/$4_${tag}_${seed}.log 2>&1" >> logs/queue_$4.txt
    done
  done
  rm -f logs/$5
  start=$(date +%s)
  cat logs/queue_$4.txt | xargs -P 3 -I{} bash -c '{}'
  end=$(date +%s)
  echo "DONE seconds=$((end-start)) results=$(find $2 -name results.json | wc -l)" > logs/$5
}
rm -f logs/P24_DONE logs/SIGLIP_DONE logs/B16_DONE
run_set models/clip-vit-base-patch32-laion outputs/c_prereg_openclip ocl_ ocl P24_DONE
run_set models/siglip-base-patch16-224     outputs/c_prereg_siglip  siglip_ s   SIGLIP_DONE
run_set models/clip-vit-base-patch16       outputs/c_prereg_b16     b16_    b16 B16_DONE
echo ALL_SETS_DONE > logs/ALL_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)

# 1. stop everything that is running
stdin, stdout, stderr = c.exec_command(
    "pkill -f 'c_driver_' ; pkill -f 'strict_freeze_control.py' ; sleep 5; "
    "rm -f /root/autodl-tmp/work/logs/P24_DONE /root/autodl-tmp/work/logs/SIGLIP_DONE /root/autodl-tmp/work/logs/B16_DONE; "
    "echo procs_after=$(ps aux | grep -c '[s]trict_freeze'); nvidia-smi --query-gpu=memory.used --format=csv,noheader",
    timeout=180)
print("cleanup:", stdout.read().decode("utf-8", "replace").strip())

# 2. clean partial outputs, upload and start the serial driver
sftp = c.open_sftp()
tmp = os.path.join(REPO, "outputs", "_driver_serial.py.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_serial.sh")
sftp.close()

stdin, stdout, stderr = c.exec_command(
    "cd %s && rm -rf outputs/c_prereg_openclip outputs/c_prereg_siglip outputs/c_prereg_b16 && "
    "sed -i 's/\\r$//' c_driver_serial.sh && chmod +x c_driver_serial.sh && "
    "(setsid nohup bash c_driver_serial.sh > logs/c_driver_serial.log 2>&1 < /dev/null &); sleep 60; "
    "echo queue=$(head -1 logs/queue_ocl.txt | grep -o 'models/[a-z0-9.-]*'); "
    "echo qlen=$(wc -l < logs/queue_ocl.txt); echo procs=$(ps aux | grep -c '[s]trict_freeze'); "
    "nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
    "grep -h -m1 'model class' logs/ocl_text_only_42.log 2>/dev/null; "
    "echo results=$(find outputs/c_prereg_openclip -name results.json 2>/dev/null | wc -l)" % REMOTE, timeout=300)
print(stdout.read().decode("utf-8", "replace").strip())
c.close()
