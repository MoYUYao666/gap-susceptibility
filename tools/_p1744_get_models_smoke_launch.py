# -*- coding: utf-8 -*-
r"""Last mile: materialise the two backbone checkpoints, free the disk, smoke, launch.

The HF cache on this instance holds only configs for CLIP B/32 (no weights), because the disk copy was partial. So:
1. download `openai/clip-vit-base-patch32` and `google/siglip-base-patch16-224` into plain directories via hf-mirror;
2. delete the 4.4 GB flickr30k images zip from the cache (the corpus is already converted, disk is at 86 %);
3. rerun the 1-epoch smoke against the real weights; on success start the detached batch.
"""
import io
import os

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westd.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "21492"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REMOTE = "/root/autodl-tmp/work"

SCRIPT = r'''# -*- coding: utf-8 -*-
import os, shutil, subprocess, sys
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
os.environ.setdefault("HF_HOME", "/root/autodl-tmp/hf")
from huggingface_hub import snapshot_download

for repo, dest in (("openai/clip-vit-base-patch32", "/root/autodl-tmp/work/models/clip-vit-base-patch32"),
                   ("google/siglip-base-patch16-224", "/root/autodl-tmp/work/models/siglip-base-patch16-224")):
    if os.path.isdir(dest) and os.path.exists(os.path.join(dest, "config.json")):
        print("already there:", dest, flush=True)
        continue
    print("downloading", repo, "->", dest, flush=True)
    snapshot_download(repo, local_dir=dest, ignore_patterns=["*.msgpack", "*.h5", "*.tflite", "*.onnx", "flax_*"])
    print("  files:", len(os.listdir(dest)), flush=True)

# free the disk: the corpus is already extracted, the source zip is no longer needed
zipblob = "/root/autodl-tmp/hf/hub/datasets--nlphuji--flickr30k"
freed = 0
for root, _, files in os.walk(zipblob):
    for f in files:
        if f.endswith(".zip") or os.path.getsize(os.path.join(root, f)) > 500 * 2**20:
            p = os.path.join(root, f)
            try:
                sz = os.path.getsize(p); os.remove(p); freed += sz
            except OSError:
                pass
print("freed MB:", round(freed / 2**20, 1), flush=True)
print("free space:", subprocess.run(["df", "-h", "/root/autodl-tmp"], capture_output=True, text=True).stdout.strip().splitlines()[-1], flush=True)
'''

SMOKE = (
    "cd %s && export HF_HOME=/root/autodl-tmp/hf HF_ENDPOINT=https://hf-mirror.com && "
    "/root/miniconda3/bin/python experiments/strict_freeze_control.py --model models/clip-vit-base-patch32 --smoke "
    "--out-dir outputs/_smoke --name smoke_ --tags both --seeds 42 --epochs 1 --max-samples 200 "
    "--batch-size 32 --skip-frozen --dg-star 2>&1 | tail -12 && echo '--- smoke results ---' && "
    "find outputs/_smoke -name results.json | head -3"
) % REMOTE

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "_get_models.py")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(SCRIPT)
sftp.put(tmp, REMOTE + "/_get_models.py")
sftp.close()

print("=== 1. checkpoints + disk ===")
stdin, stdout, stderr = c.exec_command("cd %s && /root/miniconda3/bin/python _get_models.py 2>&1 | tail -10" % REMOTE,
                                       timeout=2400)
print(stdout.read().decode("utf-8", "replace")[-2000:])
err = stderr.read().decode("utf-8", "replace")
if err.strip():
    print("--- stderr ---", err[-1200:])

print("\n=== 2. smoke ===")
stdin, stdout, stderr = c.exec_command(SMOKE, timeout=1800)
print(stdout.read().decode("utf-8", "replace")[-3000:])

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
