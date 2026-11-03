#!/usr/bin/env bash
# Fetch Qwen2.5-VL-7B in the background while the LLaVA retrain occupies the GPU.
#
# The earlier conclusion ("32 GB cannot fit Qwen-7B bf16") was reached when the measurement path still called
# `output_hidden_states=True`, which on this stack allocates far more than expected -- it produced 29.81 GiB for
# LLaVA. Whether that was the real cause for Qwen is untested, so the model is fetched now (no GPU needed) and the
# smoke test runs once the retrain frees the device.
#
# Source: the mirror, multi-connection, per the rule; sizes come from HEAD requests so no listing API is needed
# (the mirror's listing endpoint answers 403 from this container).
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
PY=/root/miniconda3/bin/python
BASE=https://hf-mirror.com/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main
DEST=/root/autodl-tmp/hf/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/main
mkdir -p "$DEST"

echo "=== which files exist on the mirror? (HEAD each) ==="
for f in config.json model.safetensors.index.json model-00001-of-00004.safetensors \
         model-00002-of-00004.safetensors model-00003-of-00004.safetensors \
         model-00004-of-00004.safetensors preprocessor_config.json generation_config.json \
         tokenizer.json tokenizer_config.json chat_template.json vocab.json merges.txt; do
  code=$(curl -sI -m 20 -o /dev/null -w '%{http_code}' "$BASE/$f" 2>/dev/null || echo ERR)
  size=$(curl -sI -m 20 "$BASE/$f" 2>/dev/null | tr -d '\r' | awk '/[Cc]ontent-[Ll]ength/ {print $2}' | tail -1)
  printf '  %-40s %s  %s\n' "$f" "$code" "${size:-?}"
done

echo
echo "=== shard list and sizes ==="
SHARDS=""
SIZES=""
for i in 00001 00002 00003 00004; do
  f="model-$i-of-00004.safetensors"
  s=$(curl -sI -m 20 "$BASE/$f" 2>/dev/null | tr -d '\r' | awk '/[Cc]ontent-[Ll]ength/ {print $2}' | tail -1)
  if [ -n "${s:-}" ] && [ "$s" -gt 1000000 ] 2>/dev/null; then
    SHARDS="${SHARDS:+$SHARDS,}$f"
    SIZES="${SIZES:+$SIZES,}$s"
    echo "  $f  $((s/1000000)) MB"
  fi
done
if [ -z "$SHARDS" ]; then
  echo "  no shards found -- Qwen2.5-VL may use a single model.safetensors; probing that"
  s=$(curl -sI -m 20 "$BASE/model.safetensors" 2>/dev/null | tr -d '\r' | awk '/[Cc]ontent-[Ll]ength/ {print $2}' | tail -1)
  echo "  model.safetensors  ${s:-?}"
  SHARDS="model.safetensors"; SIZES="${s:-0}"
fi
echo "  -> $SHARDS"
echo "  -> $SIZES"

echo
echo "=== start the multi-connection fetch in the background ==="
setsid bash -c "$PY /root/p3/tools/_p1101_parallel_fetch_any.py \
  --base '$BASE/{f}' --files '$SHARDS' --sizes '$SIZES' \
  --dest '$DEST' > /root/p3/qwen_dl.log 2>&1" < /dev/null > /dev/null 2>&1 &
disown
sleep 30
echo "--- progress after 30 s ---"
tail -3 /root/p3/qwen_dl.log 2>/dev/null | tr -d '\r'
df -h /root/autodl-tmp | tail -1
echo QWEN_FETCH_STARTED
