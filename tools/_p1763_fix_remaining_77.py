# -*- coding: utf-8 -*-
r"""Finish the SigLIP fix: the remaining hardcoded 77-token limits and a clean relaunch.

The arms now die with `CUDA error: device-side assert triggered`, the signature of an out-of-range index in the text
embedding lookup: `src/gap_susceptibility.py` and `src/lora.py` still call the processor with `max_length=77`, so after
the trainer switched the pipeline to 64 the gap and PEFT paths kept sending 77 positions into a 64-position encoder.
Fix: both files read `PEFT_MAX_SEQ_LEN` like the dataset does, then upload all three and rerun the arms (results that
already exist are skipped, so a relaunch is idempotent).
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

patched = []
for rel in ("src/lora.py", "src/gap_susceptibility.py"):
    p = os.path.join(REPO, rel)
    t = io.open(p, encoding="utf-8").read()
    if "PEFT_MAX_SEQ_LEN" in t:
        patched.append(rel)
        continue
    if "max_length=77" not in t:
        raise SystemExit("no max_length=77 in %s - inspect before patching" % rel)
    if "import os" not in t:
        lines = t.splitlines(keepends=True)
        for i, ln in enumerate(lines):
            if ln.startswith(("import ", "from ")):
                lines.insert(i, "import os\n")
                break
        t = "".join(lines)
        print("added import os to", rel)
    t = t.replace("max_length=77",
                  'max_length=int(os.environ.get("PEFT_MAX_SEQ_LEN", "77"))')
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    patched.append(rel)
    print("patched:", rel)

DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg_siglip
: > logs/queue_p3b.txt
for tag in text_only both vision_only; do
  for seed in 42 123 456 789 1012; do
    if [ -f "outputs/c_prereg_siglip/$tag/seed$seed/results.json" ]; then continue; fi
    echo "$PY experiments/strict_freeze_control.py --model models/siglip-base-patch16-224 --out-dir outputs/c_prereg_siglip --name siglip_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/p3b_${tag}_${seed}.log 2>&1" >> logs/queue_p3b.txt
  done
done
rm -f logs/P3_DONE
start=$(date +%s)
cat logs/queue_p3b.txt | xargs -P 1 -I{} bash -c '{}'
end=$(date +%s)
echo "P3_DONE seconds=$((end-start)) results=$(find outputs/c_prereg_siglip -name results.json | wc -l)" > logs/P3_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)

stdin, stdout, stderr = c.exec_command(
    "pkill -9 -f '[c]_driver_p3'; pkill -9 -f '[s]trict_freeze_control'; sleep 6; "
    "echo procs=$(ps aux | grep -c '[s]trict_freeze_control')", timeout=120)
print("stopped old run:", stdout.read().decode("utf-8", "replace").strip())

sftp = c.open_sftp()
for rel in ("src/trainer.py", "src/dataset.py", "src/lora.py", "src/gap_susceptibility.py"):
    sftp.put(os.path.join(REPO, rel), REMOTE + "/" + rel)
tmp = os.path.join(REPO, "outputs", "_driver_p3b.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_p3b.sh")
sftp.close()
print("uploaded:", ", ".join(patched), "and the P3 relaunch driver")

stdin, stdout, stderr = c.exec_command(
    "cd %s && grep -c PEFT_MAX_SEQ_LEN src/lora.py src/gap_susceptibility.py && chmod +x c_driver_p3b.sh && "
    "(setsid nohup bash c_driver_p3b.sh > logs/p3b_driver.log 2>&1 < /dev/null &); sleep 50; "
    "echo queue=$(wc -l < logs/queue_p3b.txt 2>/dev/null); "
    "echo procs=$(ps aux | grep -c '[s]trict_freeze_control'); "
    "nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
    "grep -h -m2 'Traceback\\|Error' logs/p3b_*.log 2>/dev/null | head -3" % REMOTE, timeout=300)
print(stdout.read().decode("utf-8", "replace")[-1200:])
c.close()
