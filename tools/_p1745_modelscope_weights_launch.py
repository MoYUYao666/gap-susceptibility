# -*- coding: utf-8 -*-
r"""Option 1: get the two backbone checkpoints from ModelScope (the mirror's Xet weights are unreachable),
then smoke-test and start the batch.

Tries several plausible ModelScope repo ids per model, materialises the files in work/models/<name>, and only starts
the batch when a real weight file (safetensors or .bin) is present.
"""
import io
import os

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westd.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "21492"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REMOTE = "/root/autodl-tmp/work"

FETCH = r'''# -*- coding: utf-8 -*-
import glob, os, shutil
os.environ.setdefault("MODELSCOPE_CACHE", "/root/autodl-tmp/ms")
os.environ.setdefault("MODELSCOPE_LOG_LEVEL", "30")
from modelscope.hub.snapshot_download import snapshot_download

TARGETS = [
    ("clip-vit-base-patch32", ["AI-ModelScope/clip-vit-base-patch32", "openai-mirror/clip-vit-base-patch32",
                               "damo/ofa_image-caption_coco_distilled_en"]),
    ("siglip-base-patch16-224", ["AI-ModelScope/siglip-base-patch16-224", "google-mirror/siglip-base-patch16-224"]),
]
WORK = "/root/autodl-tmp/work/models"

def has_weights(d):
    return bool(glob.glob(os.path.join(d, "*.safetensors")) or glob.glob(os.path.join(d, "*.bin")))

for name, repos in TARGETS:
    dest = os.path.join(WORK, name)
    if has_weights(dest):
        print("already present:", dest, flush=True)
        continue
    os.makedirs(dest, exist_ok=True)
    done = False
    for repo in repos:
        try:
            local = snapshot_download(repo, cache_dir="/root/autodl-tmp/ms")
        except Exception as e:
            print("  miss", repo, type(e).__name__, str(e)[:120], flush=True)
            continue
        n = 0
        for f in glob.glob(os.path.join(local, "*")):
            if os.path.isfile(f):
                shutil.copy2(f, os.path.join(dest, os.path.basename(f)))
                n += 1
        print("  copied", n, "files from", repo, "->", dest, flush=True)
        if has_weights(dest):
            done = True
            break
    print(("OK " if done else "FAILED ") + name, "| weights:", has_weights(dest),
          "| files:", len(os.listdir(dest)), flush=True)
'''

SMOKE = (
    "cd %s && export HF_HOME=/root/autodl-tmp/hf && "
    "/root/miniconda3/bin/python experiments/strict_freeze_control.py --model models/clip-vit-base-patch32 --smoke "
    "--out-dir outputs/_smoke --name smoke_ --tags both --seeds 42 --epochs 1 --max-samples 200 "
    "--batch-size 32 --skip-frozen --dg-star 2>&1 | tail -12 && echo '--- smoke results ---' && "
    "find outputs/_smoke -name results.json | head -3"
) % REMOTE

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "_fetch_ms.py")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(FETCH)
sftp.put(tmp, REMOTE + "/_fetch_ms.py")
sftp.close()

print("=== 1. ModelScope checkpoints ===")
stdin, stdout, stderr = c.exec_command("cd %s && /root/miniconda3/bin/python _fetch_ms.py 2>&1 | tail -14" % REMOTE,
                                       timeout=3000)
print(stdout.read().decode("utf-8", "replace")[-2500:])

print("\n=== 2. smoke ===")
stdin, stdout, stderr = c.exec_command(SMOKE, timeout=1800)
print(stdout.read().decode("utf-8", "replace")[-2500:])

stdin, stdout, stderr = c.exec_command("cd %s && find outputs/_smoke -name results.json | head -2" % REMOTE, timeout=120)
found = stdout.read().decode("utf-8", "replace").strip()
print("\nsmoke results:", found or "NONE")
if found:
    stdin, stdout, stderr = c.exec_command(
        "cd %s && setsid nohup bash c_driver.sh > logs/c_driver.log 2>&1 < /dev/null & sleep 12; echo launched; "
        "wc -l < logs/queue.txt; ps aux | grep -c '[s]trict_freeze'; nvidia-smi --query-gpu=memory.used --format=csv,noheader"
        % REMOTE, timeout=180)
    print("\n=== 3. batch launched ===\n" + stdout.read().decode("utf-8", "replace"))
else:
    print("\nbatch NOT started")
c.close()
