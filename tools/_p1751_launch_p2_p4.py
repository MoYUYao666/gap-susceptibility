# -*- coding: utf-8 -*-
r"""While the instance is up, run the two pre-registered arms that only need a CLIP-compatible checkpoint:

  P4 : CLIP B/16      (openai/clip-vit-base-patch16)
  P2 : OpenCLIP B/32  (laion/CLIP-ViT-B-32-laion2B-s34B-b79K, a CLIPModel)

SigLIP needs a trainer-level change (the trainer hardcodes `CLIPModel`), which is not a quick fix, so it is deferred.
Weights come from ModelScope (the HF mirror serves Xet-only weights, unreachable without a token).
"""
import io
import os

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westb.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "39308"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REMOTE = "/root/autodl-tmp/work"

FETCH = r'''# -*- coding: utf-8 -*-
import glob, os, shutil
os.environ.setdefault("MODELSCOPE_CACHE", "/root/autodl-tmp/ms")
from modelscope.hub.snapshot_download import snapshot_download

TARGETS = [
    ("clip-vit-base-patch16", ["openai-mirror/clip-vit-base-patch16", "AI-ModelScope/clip-vit-base-patch16"]),
    ("clip-vit-base-patch32-laion", ["AI-ModelScope/CLIP-ViT-B-32-laion2B-s34B-b79K",
                                     "laion-mirror/CLIP-ViT-B-32-laion2B-s34B-b79K"]),
]
WORK = "/root/autodl-tmp/work/models"

def has_weights(d):
    return bool(glob.glob(os.path.join(d, "*.safetensors")) or glob.glob(os.path.join(d, "*.bin")))

for name, repos in TARGETS:
    dest = os.path.join(WORK, name)
    if has_weights(dest):
        print("present:", name, flush=True); continue
    os.makedirs(dest, exist_ok=True)
    ok = False
    for repo in repos:
        try:
            local = snapshot_download(repo, cache_dir="/root/autodl-tmp/ms")
        except Exception as e:
            print("  miss", repo, str(e)[:90], flush=True); continue
        n = 0
        for f in glob.glob(os.path.join(local, "*")):
            if os.path.isfile(f):
                shutil.copy2(f, os.path.join(dest, os.path.basename(f))); n += 1
        print("  copied", n, "from", repo, flush=True)
        if has_weights(dest):
            ok = True; break
    print(("OK " if ok else "FAILED ") + name, flush=True)
'''

DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg_b16 outputs/c_prereg_openclip
: > logs/queue_p24.txt
MODEL=/root/autodl-tmp/work/models/clip-vit-base-patch16
if ls $MODEL/*.safetensors $MODEL/*.bin >/dev/null 2>&1; then
  for tag in text_only both vision_only; do for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model $MODEL --out-dir outputs/c_prereg_b16 --name b16_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/b16_${tag}_${seed}.log 2>&1" >> logs/queue_p24.txt
  done; done
fi
MODEL2=/root/autodl-tmp/work/models/clip-vit-base-patch32-laion
if ls $MODEL2/*.safetensors $MODEL2/*.bin >/dev/null 2>&1; then
  for tag in text_only both vision_only; do for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model $MODEL2 --out-dir outputs/c_prereg_openclip --name ocl_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/ocl_${tag}_${seed}.log 2>&1" >> logs/queue_p24.txt
  done; done
fi
start=$(date +%s)
cat logs/queue_p24.txt | xargs -P 3 -I{} bash -c '{}'
end=$(date +%s)
echo "P24_DONE seconds=$((end-start)) arms=$(wc -l < logs/queue_p24.txt) results=$(find outputs/c_prereg_b16 outputs/c_prereg_openclip -name results.json 2>/dev/null | wc -l)" > logs/P24_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
for name, text in (("_fetch_p24.py", FETCH), ("_driver_p24.sh", DRIVER)):
    p = os.path.join(base, name)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    sftp.put(p, REMOTE + "/" + name)
sftp.close()

print("=== weights ===")
stdin, stdout, stderr = c.exec_command("cd %s && /root/miniconda3/bin/python _fetch_p24.py 2>&1 | tail -10" % REMOTE,
                                       timeout=2400)
print(stdout.read().decode("utf-8", "replace")[-1500:])

print("\n=== launch P2/P4 ===")
stdin, stdout, stderr = c.exec_command(
    "cd %s && sed -i 's/\\r$//' _driver_p24.sh && chmod +x _driver_p24.sh && "
    "(setsid nohup bash _driver_p24.sh > logs/c_driver_p24.log 2>&1 < /dev/null &); sleep 5; "
    "echo started; wc -l < logs/queue_p24.txt" % REMOTE, timeout=120)
print(stdout.read().decode("utf-8", "replace").strip())
c.close()
