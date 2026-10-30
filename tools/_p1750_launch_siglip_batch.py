# -*- coding: utf-8 -*-
r"""Launch the SigLIP half of the pre-registered batch (P3).

The earlier `KeyError: 'vision'` was NOT a SigLIP block-mapping problem: the traceback pointed at
`CONFIGS[tag]` with tag='vision', i.e. my invalid tag name. `src/lora.py` discovers towers with
`hasattr(model, 'vision_model' / 'text_model')`, which `SiglipModel` also exposes. So the same protocol runs
unchanged with the correct tags, only `--model` and `--out-dir` change.
"""
import io
import os

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westb.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "39308"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REMOTE = "/root/autodl-tmp/work"

DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg_siglip
: > logs/queue_siglip.txt
for tag in text_only both vision_only; do
  for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model models/siglip-base-patch16-224 --out-dir outputs/c_prereg_siglip --name siglip_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/s_${tag}_${seed}.log 2>&1" >> logs/queue_siglip.txt
  done
done
start=$(date +%s)
cat logs/queue_siglip.txt | xargs -P 3 -I{} bash -c '{}'
end=$(date +%s)
echo "SIGLIP_DONE seconds=$((end-start)) results=$(find outputs/c_prereg_siglip -name results.json | wc -l)" > logs/SIGLIP_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "_driver_siglip.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_siglip.sh")
sftp.close()

stdin, stdout, stderr = c.exec_command(
    "cd %s && sed -i 's/\\r$//' c_driver_siglip.sh && chmod +x c_driver_siglip.sh && "
    "(setsid nohup bash c_driver_siglip.sh > logs/c_driver_siglip.log 2>&1 < /dev/null &); sleep 3; echo started"
    % REMOTE, timeout=120)
print(stdout.read().decode("utf-8", "replace").strip())

stdin, stdout, stderr = c.exec_command(
    "sleep 75; cd %s; echo queue=$(wc -l < logs/queue_siglip.txt); echo procs=$(ps aux | grep -c '[s]trict_freeze'); "
    "nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
    "echo results=$(find outputs/c_prereg_siglip -name results.json 2>/dev/null | wc -l); "
    "for f in $(ls -t logs/s_*.log 2>/dev/null | head -2); do echo \"--- $f\"; tail -1 \"$f\"; done; "
    "grep -h -m2 'Traceback\\|KeyError\\|Error' logs/s_*.log 2>/dev/null | head -3" % REMOTE, timeout=420)
print(stdout.read().decode("utf-8", "replace")[-2000:])
c.close()
