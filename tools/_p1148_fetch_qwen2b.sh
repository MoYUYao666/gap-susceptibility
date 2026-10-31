#!/usr/bin/env bash
# Fetch Qwen2-VL-2B-Instruct (the model behind supplement Table E) with many connections.
#
# The mirror answered 307 on a plain HEAD, so sizes come from `curl -sIL` (follow redirects) and the shard list
# comes from the checkpoint's own index file rather than being guessed.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
PY=/root/miniconda3/bin/python
BASE=https://hf-mirror.com/Qwen/Qwen2-VL-2B-Instruct/resolve/main
DEST=/root/autodl-tmp/hf/hub/models--Qwen--Qwen2-VL-2B-Instruct/snapshots/main
mkdir -p "$DEST" /root/p3/tools /root/p3/outputs

echo "=== index file ==="
curl -sSL -m 120 -o "$DEST/model.safetensors.index.json" "$BASE/model.safetensors.index.json"
ls -la "$DEST/model.safetensors.index.json"
SHARDS=$($PY - "$DEST/model.safetensors.index.json" <<'PYEOF'
import json, sys
try:
    idx = json.load(open(sys.argv[1]))
    print(",".join(sorted(set(idx.get("weight_map", {}).values()))))
except Exception:
    print("")
PYEOF
)
if [ -z "$SHARDS" ]; then
  echo "  no index; assuming a single model.safetensors"
  SHARDS="model.safetensors"
fi
echo "  shards: $SHARDS"

echo "=== sizes (redirects followed) ==="
SIZES=""
for f in $(echo "$SHARDS" | tr ',' ' '); do
  s=$(curl -sIL -m 30 "$BASE/$f" 2>/dev/null | tr -d '\r' | awk '/[Cc]ontent-[Ll]ength: *[0-9]+/ {print $2}' | tail -1)
  echo "  $f  ${s:-?}"
  SIZES="${SIZES:+$SIZES,}${s:-0}"
done

echo "=== small files ==="
for f in config.json generation_config.json preprocessor_config.json tokenizer.json \
         tokenizer_config.json chat_template.json vocab.json merges.txt; do
  [ -s "$DEST/$f" ] || curl -sSL -m 180 -o "$DEST/$f" "$BASE/$f" 2>/dev/null
  printf '  %-30s %s bytes\n' "$f" "$(stat -c %s "$DEST/$f" 2>/dev/null || echo MISSING)"
done

echo "=== multi-connection fetch ==="
pkill -9 -f _p1101_parallel_fetch_any || true
sleep 2
setsid bash -c "$PY /root/p3/tools/_p1101_parallel_fetch_any.py \
  --base '$BASE/{f}' --files '$SHARDS' --sizes '$SIZES' \
  --dest '$DEST' > /root/p3/qwen2b_dl.log 2>&1" < /dev/null > /dev/null 2>&1 &
disown
sleep 40
echo "--- progress after 40 s ---"
tail -3 /root/p3/qwen2b_dl.log 2>/dev/null | tr -d '\r'
df -h /root/autodl-tmp | tail -1
echo QWEN2B_FETCH_STARTED
