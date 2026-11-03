#!/usr/bin/env bash
# Fetch the weights from the mirror with many connections, using the file list verified on the earlier host.
#
# The mirror's listing API answers 403 Forbidden from this container, so the file names and sizes are taken from
# the inventory that `HubApi().get_model_files` returned for the same repository yesterday and confirmed against
# the actual downloads (model-00001/02/03 plus tokenizer.json). Sizes are passed explicitly so no HEAD request is
# needed; the fetcher still verifies each assembled file against the size it is given.
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

SHARDS=model-00001-of-00003.safetensors,model-00002-of-00003.safetensors,model-00003-of-00003.safetensors
SIZES=4992930200,4957878440,4176137408

echo "=== start the multi-connection shard fetch (32 workers) ==="
pkill -9 -f _p1101_parallel_fetch_any || true
sleep 2
setsid bash -c "$PY /root/p3/tools/_p1101_parallel_fetch_any.py \
  --base '$BASE/{f}' --files '$SHARDS' --sizes '$SIZES' \
  --dest '$DEST/blobs' > /root/p3/mirror_mt.log 2>&1" < /dev/null > /dev/null 2>&1 &
disown
sleep 40
echo "--- progress ---"
tail -5 /root/p3/mirror_mt.log 2>/dev/null | tr -d '\r'

echo "=== small files (single connection is enough) ==="
for f in config.json generation_config.json preprocessor_config.json processor_config.json \
         tokenizer.json tokenizer_config.json special_tokens_map.json chat_template.json \
         model.safetensors.index.json; do
  out="$SNAP/$f"
  [ -s "$out" ] && { echo "  present $f"; continue; }
  if curl -sSL -m 180 -o "$out" "$BASE/$f" 2>/dev/null && [ -s "$out" ]; then
    echo "  got $f ($(stat -c %s "$out") bytes)"
  else
    rm -f "$out"; echo "  absent $f"
  fi
done

echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
echo MIRROR_MT_V2_STARTED
