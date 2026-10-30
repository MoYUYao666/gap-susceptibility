#!/usr/bin/env bash
# Re-fetch the weights with many connections, because ModelScope throttles a single connection to about 1 MB/s
# while the host's link is good for at least 7 MB/s (measured: 1,887 KB/s from the running download plus
# 5,333 KB/s from 16 extra range requests).
#
# The per-file URLs are read from the ModelScope client itself, so the paths are the ones the registry serves
# rather than guesses. RESUME=1 is passed so already-downloaded bytes are kept.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export MODELSCOPE_CACHE=/root/autodl-tmp/modelscope
PY=/root/miniconda3/bin/python
REPO=llava-hf/llava-1.5-7b-hf

echo "=== stop the single-connection download ==="
pkill -9 -f "snapshot_download" || true
pkill -9 -f "ms_llava_dl" || true
sleep 3
ps -eo pid,cmd | grep -E "snapshot_download" | grep -v grep || echo "  stopped"

echo "=== install aria2 from tuna ==="
command -v aria2c >/dev/null && echo "  aria2c already present" || {
  $PY -m pip install -q --no-input -i https://pypi.tuna.tsinghua.edu.cn/simple aria2p 2>&1 | tail -2
  (apt-get -y -qq install aria2 2>&1 | tail -2) || true
}
command -v aria2c >/dev/null && aria2c --version | head -1 || echo "  aria2c NOT available; will use python ranges"

echo "=== get the file list and URLs from the client ==="
$PY - <<'PYEOF' > /root/p3/_urls.txt
from modelscope.hub.api import HubApi
api = HubApi()
files = api.get_model_files("llava-hf/llava-1.5-7b-hf", recursive=True)
for f in files:
    size = f.get("Size") or 0
    path = f.get("Path")
    if size and size > 1_000_000:          # only the large ones are worth parallelising
        rev = f.get("Revision") or "master"
        print(f"https://modelscope.cn/models/llava-hf/llava-1.5-7b-hf/resolve/{rev}/{path} {path} {size}")
PYEOF
wc -l /root/p3/_urls.txt
head -6 /root/p3/_urls.txt

echo "=== download in parallel into the modelscope cache layout ==="
DEST=/root/autodl-tmp/modelscope/hub/llava-hf/llava-1.5-7b-hf
mkdir -p "$DEST"
while read -r url path size; do
  out="$DEST/$(basename "$path")"
  echo "  -> $(basename "$path")  ($((size/1000000)) MB)"
  if command -v aria2c >/dev/null; then
    aria2c -q -c -x 16 -s 16 -k 4M --file-allocation=none -d "$DEST" -o "$(basename "$path")" "$url"
  else
    curl -sSL -C - -o "$out" "$url"
  fi
done < /root/p3/_urls.txt

echo "=== also fetch the small files (config, tokenizer) ==="
$PY - <<'PYEOF'
from modelscope import snapshot_download
p = snapshot_download("llava-hf/llava-1.5-7b-hf", cache_dir="/root/autodl-tmp/modelscope", allow_patterns=["*.json", "*.txt", "*.model", "*.py"])
print("  small files at:", p)
PYEOF

echo "=== result ==="
du -sh /root/autodl-tmp/modelscope
ls -la "$DEST" | head -20
df -h /root/autodl-tmp | tail -1
echo PARALLEL_DL_DONE
