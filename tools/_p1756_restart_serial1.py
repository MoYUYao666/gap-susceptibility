# -*- coding: utf-8 -*-
r"""Restart the remaining pre-registered arms at parallelism 1 with the allocator fix.

Diagnosis from the logs: the B/16 batch died with `torch.OutOfMemoryError` - one process held 20.05 GiB while the second
held 11.30 GiB against a 31.48 GiB card, i.e. the `both`-tower arms of CLIP B/16 (16x16 patches = 4x the tokens of
B/32) are much heavier than the B/32 arms the 2-way decision was measured on. SigLIP's batch also produced no results.

Fix: run strictly one arm at a time (`-P 1`) with `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, which fits a
single 20-25 GiB arm. Only the missing arms are queued: OpenCLIP is complete (15/15), B/16 needs its remaining arms,
SigLIP all 15. Progress is idempotent - an arm whose results.json already exists is skipped.
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
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
mkdir -p logs
: > logs/queue_rest.txt
for spec in "b16:models/clip-vit-base-patch16:outputs/c_prereg_b16" "sig:models/siglip-base-patch16-224:outputs/c_prereg_siglip"; do
  name=${spec%%:*}; rest=${spec#*:}; model=${rest%%:*}; out=${rest##*:}
  for tag in text_only both vision_only; do
    for seed in 42 123 456 789 1012; do
      if [ -f "$out/$tag/seed$seed/results.json" ]; then continue; fi
      echo "$PY experiments/strict_freeze_control.py --model $model --out-dir $out --name ${name}_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/r_${name}_${tag}_${seed}.log 2>&1" >> logs/queue_rest.txt
    done
  done
done
start=$(date +%s)
cat logs/queue_rest.txt | xargs -P 1 -I{} bash -c '{}'
end=$(date +%s)
echo "REST_DONE seconds=$((end-start)) arms=$(wc -l < logs/queue_rest.txt)" > logs/REST_DONE
echo "b16=$(find outputs/c_prereg_b16 -name results.json | wc -l) sig=$(find outputs/c_prereg_siglip -name results.json | wc -l)" >> logs/REST_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(REPO, "outputs", "_driver_rest.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_rest.sh")
sftp.close()

stdin, stdout, stderr = c.exec_command(
    "cd %s && chmod +x c_driver_rest.sh && rm -f logs/SIGLIP_DONE logs/B16_DONE && "
    "(setsid nohup bash c_driver_rest.sh > logs/rest.log 2>&1 < /dev/null &); sleep 45; "
    "echo queue=$(wc -l < logs/queue_rest.txt 2>/dev/null); "
    "echo procs=$(ps aux | grep -c '[s]trict_freeze_control'); "
    "nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
    "echo b16=$(find outputs/c_prereg_b16 -name results.json | wc -l) sig=$(find outputs/c_prereg_siglip -name results.json 2>/dev/null | wc -l); "
    "grep -h -m1 'Traceback\\|KeyError' logs/r_*.log 2>/dev/null | head -2" % REMOTE, timeout=300)
print(stdout.read().decode("utf-8", "replace").strip())
c.close()
