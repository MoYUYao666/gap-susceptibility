# -*- coding: utf-8 -*-
r"""Bring the flickr30k corpus onto the instance, then smoke-test and launch the pre-registered batch.

1. download `nlphuji/flickr30k` through hf-mirror (the only working route on these hosts);
2. stream-convert it into the corpus layout the training code expects:
      flickr30k/flickr30k.json      [{"image": "...", "captions": [5 captions]}]
      flickr30k/flickr30k-images/   the jpgs actually used
   (only the images needed for the 5000-sample runs are written, so the conversion stays bounded);
3. rerun the 1-epoch smoke; on success, launch the detached batch via the already-uploaded driver.
"""
import io
import os

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westd.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "21492"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REMOTE = "/root/autodl-tmp/work"

CONVERT = r'''# -*- coding: utf-8 -*-
import io, json, os, sys
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", "/root/autodl-tmp/hf")
from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq
from PIL import Image

OUT = "/root/autodl-tmp/work/flickr30k"
IMG = os.path.join(OUT, "flickr30k-images")
os.makedirs(IMG, exist_ok=True)
TARGET_CAPTIONS = 5000

from huggingface_hub import HfApi, snapshot_download
files = HfApi().list_repo_files("nlphuji/flickr30k", repo_type="dataset")
print("repo files:", files[:12], flush=True)
local = snapshot_download("nlphuji/flickr30k", repo_type="dataset", allow_patterns=["*.parquet"])
import glob
paths = sorted(glob.glob(os.path.join(local, "**", "*.parquet"), recursive=True))
print("parquet shards:", [os.path.relpath(p, local) for p in paths], flush=True)

pf = pq.ParquetFile(paths[0])
cols = pf.schema.names
print("columns:", cols, flush=True)
img_col = next((c for c in cols if c in ("image", "img", "jpg")), None)
cap_col = next((c for c in cols if c in ("caption", "captions", "sent")), None)
id_col = next((c for c in cols if c in ("img_id", "image_id", "filename")), None)
assert img_col and cap_col and id_col, cols

by_img = {}
order = []
written = 0
for batch in pf.iter_batches(batch_size=32):
    d = batch.to_pydict()
    n = len(d[cap_col])
    for i in range(n):
        key = str(d[id_col][i])
        cap = d[cap_col][i]
        if isinstance(cap, list):
            cap = cap[0] if cap else ""
        if key not in by_img:
            raw = d[img_col][i]
            if isinstance(raw, dict):
                raw = raw.get("bytes") or raw.get("path")
            if isinstance(raw, bytes):
                with open(os.path.join(IMG, key + ".jpg"), "wb") as f:
                    f.write(raw)
                written += 1
            elif isinstance(raw, str) and os.path.isfile(raw):
                Image.open(raw).convert("RGB").save(os.path.join(IMG, key + ".jpg"), "JPEG")
                written += 1
            by_img[key] = []
            order.append(key)
        by_img[key].append(str(cap))
    if sum(len(v) for v in by_img.values()) >= TARGET_CAPTIONS:
        break

data = [{"image": k + ".jpg", "captions": by_img[k]} for k in order]
json.dump(data, io.open(os.path.join(OUT, "flickr30k.json"), "w", encoding="utf-8"), indent=0)
print("images written:", written, "| entries:", len(data), "| captions:", sum(len(v) for v in by_img.values()), flush=True)
'''

SMOKE = (
    "cd %s && export HF_HOME=/root/autodl-tmp/hf HF_ENDPOINT=https://hf-mirror.com && "
    "CLIP=$(ls -d /root/autodl-tmp/hf/hub/models--openai--clip-vit-base-patch32/snapshots/* | head -1) && "
    "/root/miniconda3/bin/python experiments/strict_freeze_control.py --model \"$CLIP\" --smoke "
    "--out-dir outputs/_smoke --name smoke_ --tags both --seeds 42 --epochs 1 --max-samples 200 "
    "--batch-size 32 --skip-frozen --dg-star 2>&1 | tail -8 && echo '--- smoke results ---' && "
    "find outputs/_smoke -name results.json | head -3"
) % REMOTE

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "_convert_flickr.py")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(CONVERT)
sftp.put(tmp, REMOTE + "/_convert_flickr.py")
sftp.close()

print("=== 1. download + convert (hf-mirror) ===")
stdin, stdout, stderr = c.exec_command(
    "cd %s && /root/miniconda3/bin/python _convert_flickr.py 2>&1 | tail -12" % REMOTE, timeout=3000)
print(stdout.read().decode("utf-8", "replace")[-2500:])
err = stderr.read().decode("utf-8", "replace")
if err.strip():
    print("--- stderr ---", err[-1500:])

print("\n=== 2. smoke ===")
stdin, stdout, stderr = c.exec_command(SMOKE, timeout=1500)
print(stdout.read().decode("utf-8", "replace")[-2500:])
err = stderr.read().decode("utf-8", "replace")
if err.strip():
    print("--- stderr ---", err[-1500:])

stdin, stdout, stderr = c.exec_command("cd %s && find outputs/_smoke -name results.json | head -2" % REMOTE, timeout=120)
found = stdout.read().decode("utf-8", "replace").strip()
print("\nsmoke results:", found or "NONE")

if found:
    stdin, stdout, stderr = c.exec_command(
        "cd %s && setsid nohup bash c_driver.sh > logs/c_driver.log 2>&1 < /dev/null & sleep 10; "
        "echo launched; wc -l < logs/queue.txt; ps aux | grep -c '[s]trict_freeze'" % REMOTE, timeout=180)
    print("\n=== 3. batch launched ===\n" + stdout.read().decode("utf-8", "replace"))
else:
    print("\nbatch NOT started (smoke failed)")
c.close()
