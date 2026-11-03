#!/usr/bin/env bash
# Get the weights from the mirror with many connections, and install the inference stack from tuna.
#
# Measured on this host (2026-08-17 morning): mirror single-connection ~1.6 KB/s, mirror with 16 connections
# 6.5 MB/s, tuna 11.4 MB/s. So both the weights (mirror) and the packages (tuna) use the fastest available path,
# and the weights go through the multi-connection splitter rather than `snapshot_download`.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_ENDPOINT=https://hf-mirror.com
PY=/root/miniconda3/bin/python
BASE=https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main
DEST=/root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf
SNAP=$DEST/snapshots/main
mkdir -p "$DEST/blobs" "$SNAP"

echo "=== 1. install the stack from tuna (11.4 MB/s measured) ==="
$PY -m pip install -q --no-input -i https://pypi.tuna.tsinghua.edu.cn/simple \
    "transformers==5.16.1" "peft==0.20.0" "accelerate==1.14.0" sentencepiece protobuf 2>&1 | tail -3
$PY -c "
import importlib
for m in ('transformers','peft','accelerate','torch','torchvision'):
    try: print('  %-14s %s' % (m, importlib.import_module(m).__version__))
    except Exception as e: print('  %-14s MISSING' % m)
"

echo "=== 2. mirror file list and sizes ==="
$PY - <<'PYEOF' > /root/p3/_mirror_files.tsv
import json, urllib.request
url = "https://hf-mirror.com/api/models/llava-hf/llava-1.5-7b-hf"
with urllib.request.urlopen(url, timeout=60) as r:
    info = json.loads(r.read())
for s in info.get("siblings", []):
    name = s.get("rfilename")
    if name:
        print(name)
PYEOF
wc -l < /root/p3/_mirror_files.tsv
cat /root/p3/_mirror_files.tsv

echo "=== 3. big shards, multi-connection ==="
SHARDS=$(grep -E '\.safetensors$' /root/p3/_mirror_files.tsv | tr '\n' ',' | sed 's/,$//')
echo "  shards: $SHARDS"
setsid bash -c "$PY /root/p3/tools/_p1101_parallel_fetch_any.py \
  --base '$BASE/{f}' --files '$SHARDS' --sizes 4992930200,4957878440,4176137408 \
  --dest '$DEST/blobs' > /root/p3/mirror_mt.log 2>&1" < /dev/null > /dev/null 2>&1 &
disown
sleep 30
echo "=== progress after 30 s ==="
tail -4 /root/p3/mirror_mt.log 2>/dev/null | tr -d '\r'
du -sh /root/autodl-tmp/hf 2>/dev/null

echo "=== 4. small files, single connection (they are tiny) ==="
while read -r f; do
  case "$f" in *.safetensors) continue;; esac
  out="$SNAP/$f"
  mkdir -p "$(dirname "$out")"
  [ -s "$out" ] && continue
  curl -sSL -m 120 -o "$out" "$BASE/$f" 2>/dev/null && echo "  got $f ($(stat -c %s "$out") bytes)" || echo "  FAILED $f"
done < /root/p3/_mirror_files.tsv

echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
echo MIRROR_MT_STARTED
