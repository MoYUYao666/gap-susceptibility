# -*- coding: utf-8 -*-
r"""ModelScope/HF-mirror route for the flickr30k corpus, then smoke + batch launch.

The mirror exposes `flickr30k-images.zip` (images) and `flickr_annotations_30k.csv` (annotations), which is enough to
build the corpus layout the training code expects:
    work/flickr30k/flickr30k.json      [{"image": "name.jpg", "captions": [5]}]
    work/flickr30k/flickr30k-images/   jpgs
Only the first 1000 images (5000 captions) are materialised, which is all the 5000-sample runs touch.
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
import glob, io, json, os, zipfile
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", "/root/autodl-tmp/hf")
from huggingface_hub import hf_hub_download

OUT = "/root/autodl-tmp/work/flickr30k"
IMG = os.path.join(OUT, "flickr30k-images")
os.makedirs(IMG, exist_ok=True)

csv_path = hf_hub_download("nlphuji/flickr30k", "flickr_annotations_30k.csv", repo_type="dataset")
print("csv:", csv_path, os.path.getsize(csv_path) // 1024, "KB", flush=True)

import pandas as pd
df = pd.read_csv(csv_path)
print("csv columns:", list(df.columns), "rows:", len(df), flush=True)
fname_col = "filename" if "filename" in df.columns else df.columns[3]
cap_col = "captions" if "captions" in df.columns else ("raw" if "raw" in df.columns else df.columns[-1])

def caps_of(v):
    if isinstance(v, list):
        return [str(x) for x in v]
    s = str(v).strip()
    if s.startswith("["):
        try:
            return [str(x) for x in json.loads(s)]
        except Exception:
            pass
    return [s]

groups = {}
order = []
for fn, cv in zip(df[fname_col].tolist(), df[cap_col].tolist()):
    fn = str(fn)
    if fn not in groups:
        groups[fn] = []
        order.append(fn)
    groups[fn].extend(caps_of(cv))
    if len(order) >= 1000:
        break
print("images selected:", len(order), "| captions:", sum(len(groups[k]) for k in order), flush=True)

zp = hf_hub_download("nlphuji/flickr30k", "flickr30k-images.zip", repo_type="dataset")
print("zip:", zp, os.path.getsize(zp) / 2**20, "MB", flush=True)
need = {fn for fn in order}
done = set()
with zipfile.ZipFile(zp) as z:
    names = z.namelist()
    print("zip entries:", len(names), "first:", names[:3], flush=True)
    for n in names:
        base = os.path.basename(n)
        if base in need and base not in done:
            with z.open(n) as src, open(os.path.join(IMG, base), "wb") as dst:
                dst.write(src.read())
            done.add(base)
print("images extracted:", len(done), flush=True)

data = [{"image": fn, "captions": groups[fn]} for fn in order if fn in done]
json.dump(data, io.open(os.path.join(OUT, "flickr30k.json"), "w", encoding="utf-8"), indent=0)
print("wrote flickr30k.json entries:", len(data), "| images on disk:", len(os.listdir(IMG)), flush=True)
'''

SMOKE = (
    "cd %s && export HF_HOME=/root/autodl-tmp/hf HF_ENDPOINT=https://hf-mirror.com && "
    "CLIP=$(ls -d /root/autodl-tmp/hf/hub/models--openai--clip-vit-base-patch32/snapshots/* | head -1) && "
    "/root/miniconda3/bin/python experiments/strict_freeze_control.py --model \"$CLIP\" --smoke "
    "--out-dir outputs/_smoke --name smoke_ --tags both --seeds 42 --epochs 1 --max-samples 200 "
    "--batch-size 32 --skip-frozen --dg-star 2>&1 | tail -10 && echo '--- smoke results ---' && "
    "find outputs/_smoke -name results.json | head -3"
) % REMOTE

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "_convert_ms.py")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(CONVERT)
sftp.put(tmp, REMOTE + "/_convert_ms.py")
sftp.close()

print("=== download + convert (hf-mirror) ===")
stdin, stdout, stderr = c.exec_command("cd %s && /root/miniconda3/bin/python _convert_ms.py 2>&1 | tail -14" % REMOTE,
                                       timeout=3600)
print(stdout.read().decode("utf-8", "replace")[-3000:])
err = stderr.read().decode("utf-8", "replace")
if err.strip():
    print("--- stderr ---", err[-2000:])

print("\n=== smoke ===")
stdin, stdout, stderr = c.exec_command(SMOKE, timeout=1800)
print(stdout.read().decode("utf-8", "replace")[-3000:])

stdin, stdout, stderr = c.exec_command("cd %s && find outputs/_smoke -name results.json | head -2" % REMOTE, timeout=120)
found = stdout.read().decode("utf-8", "replace").strip()
print("\nsmoke results:", found or "NONE")
if found:
    stdin, stdout, stderr = c.exec_command(
        "cd %s && setsid nohup bash c_driver.sh > logs/c_driver.log 2>&1 < /dev/null & sleep 10; echo launched; "
        "wc -l < logs/queue.txt; ps aux | grep -c '[s]trict_freeze'" % REMOTE, timeout=180)
    print("\n=== batch launched ===\n" + stdout.read().decode("utf-8", "replace"))
else:
    print("\nbatch NOT started")
c.close()
