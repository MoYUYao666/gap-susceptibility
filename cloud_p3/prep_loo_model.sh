#!/bin/bash
set -u
BASE=/root/autodl-tmp/p3work
cd $BASE
REPO=llava-hf/llava-onevision-qwen2-0.5b-instruct-hf
OUT=models/loo-0.5b
mkdir -p $OUT
curl -s -m 60 "https://hf-mirror.com/api/models/$REPO" -o /tmp/loo_api.json
/root/miniconda3/bin/python - <<'PY'
import json, os, subprocess
BASE = "/root/autodl-tmp/p3work"
REPO = "llava-hf/llava-onevision-qwen2-0.5b-instruct-hf"
OUT = os.path.join(BASE, "models", "loo-0.5b")
d = json.load(open("/tmp/loo_api.json"))
files = [s["rfilename"] for s in d.get("siblings", [])]
print("files:", files, flush=True)
for f in files:
    if f.startswith("."):
        continue
    dst = os.path.join(OUT, f)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    url = "https://hf-mirror.com/%s/resolve/main/%s" % (REPO, f)
    subprocess.run(["curl", "-sL", "-m", "600", "-o", dst, url], check=False)
    print(f, os.path.getsize(dst) if os.path.exists(dst) else "MISSING", flush=True)
print("LOO_DOWNLOAD_DONE")
PY
