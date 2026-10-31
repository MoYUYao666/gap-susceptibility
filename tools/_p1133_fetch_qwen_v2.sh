#!/usr/bin/env bash
# Resolve Qwen2.5-VL's real shard list and sizes, then fetch them with many connections.
#
# The previous probe used `curl -sI` without `-L`, so every HEAD returned 307 with no Content-Length and the sizes
# came out as garbage (15 bytes). Following redirects fixes that. The shard names come from the checkpoint's own
# `model.safetensors.index.json` rather than being guessed, since Qwen2.5-VL-7B does not use a single file.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
PY=/root/miniconda3/bin/python
BASE=https://hf-mirror.com/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main
DEST=/root/autodl-tmp/hf/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/main
mkdir -p "$DEST"

echo "=== fetch the index file ==="
curl -sSL -m 120 -o "$DEST/model.safetensors.index.json" "$BASE/model.safetensors.index.json"
ls -la "$DEST/model.safetensors.index.json"
head -c 300 "$DEST/model.safetensors.index.json"; echo

echo "=== shard list from the index ==="
SHARDS=$($PY - "$DEST/model.safetensors.index.json" <<'PYEOF'
import json, sys
idx = json.load(open(sys.argv[1]))
names = sorted(set(idx.get("weight_map", {}).values()))
print(",".join(names))
PYEOF
)
echo "  shards: $SHARDS"

echo "=== sizes via HEAD with redirects followed ==="
SIZES=""
for f in $(echo "$SHARDS" | tr ',' ' '); do
  s=$(curl -sIL -m 30 "$BASE/$f" 2>/dev/null | tr -d '\r' | awk '/[Cc]ontent-[Ll]ength: *[0-9]+/ {print $2}' | tail -1)
  echo "  $f  ${s:-?}"
  SIZES="${SIZES:+$SIZES,}${s:-0}"
done
echo "  sizes: $SIZES"

echo "=== clear the failed attempt and fetch ==="
rm -rf "$DEST"/model.safetensors.parts
pkill -9 -f _p1101_parallel_fetch_any || true
sleep 2
setsid bash -c "$PY /root/p3/tools/_p1101_parallel_fetch_any.py \
  --base '$BASE/{f}' --files '$SHARDS' --sizes '$SIZES' \
  --dest '$DEST' > /root/p3/qwen_dl.log 2>&1" < /dev/null > /dev/null 2>&1 &
disown
sleep 45
echo "--- progress after 45 s ---"
tail -4 /root/p3/qwen_dl.log 2>/dev/null | tr -d '\r'
df -h /root/autodl-tmp | tail -1
echo QWEN_FETCH_V2
