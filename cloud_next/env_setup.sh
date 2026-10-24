#!/bin/bash
# Cloud round setup: probe the mirrors, pin the caches to the data disk, fetch the models on the server.
# Repository rules: models are downloaded ON THE SERVER (never uploaded from the laptop), the mirror is tried
# first and chosen by measured throughput, and every large cache lives on the data disk.
set -uo pipefail

BASE="${BASE:-/root/autodl-tmp/p3work}"
DISK="${DISK:-/root/autodl-tmp}"
PY="${PY:-python}"

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HOME="$DISK/hf"
export MODELSCOPE_CACHE="$DISK/ms_cache"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-1}"
export PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
export PIP_CACHE_DIR="$DISK/pipcache"
export PYTHONIOENCODING=utf-8
export PYTORCH_ALLOC_CONF=expandable_segments:True

mkdir -p "$HF_HOME" "$MODELSCOPE_CACHE" "$PIP_CACHE_DIR" "$BASE/cloud_next/logs"

echo "== hardware =="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true
echo "== disk =="
df -h "$DISK" | tail -1

echo "== mirror probe (12 s each; choose by measured throughput, not by habit) =="
probe() {
  local name="$1" url="$2"
  local bps
  bps=$(curl -sL -m 12 -o /dev/null -w '%{speed_download}' "$url" 2>/dev/null || echo 0)
  awk -v n="$name" -v b="${bps:-0}" 'BEGIN{printf "   %-28s %8.2f MB/s\n", n, b/1048576}'
}
probe "hf-mirror.com"        "https://hf-mirror.com/Qwen/Qwen2-VL-2B-Instruct/resolve/main/config.json"
probe "modelscope.cn"        "https://modelscope.cn/api/v1/models/Qwen/Qwen2-VL-2B-Instruct/repo?Revision=master&FilePath=config.json"
probe "pypi.tuna (index)"    "https://pypi.tuna.tsinghua.edu.cn/simple/"

fetch_hf() {
  local repo="$1"
  echo "   fetch(hf-mirror): $repo"
  "$PY" - "$repo" <<'PYEOF'
import sys
from huggingface_hub import snapshot_download
p = snapshot_download(sys.argv[1], max_workers=8, resume_download=True)
print("     ->", p)
PYEOF
}

fetch_ms() {
  local repo="$1"
  echo "   fetch(modelscope): $repo"
  "$PY" - "$repo" <<'PYEOF'
import sys
from modelscope import snapshot_download
p = snapshot_download(sys.argv[1])
print("     ->", p)
PYEOF
}

fetch_any() {
  local hf_repo="$1" ms_repo="${2:-$1}"
  if ! fetch_hf "$hf_repo"; then
    echo "   hf-mirror failed or too slow for $hf_repo; falling back to ModelScope"
    fetch_ms "$ms_repo" || echo "   !! could not fetch $hf_repo - check the repository id with HubApi().get_model_files()"
  fi
}

echo "== models (about 46 GB total; the 7B decoders dominate) =="
fetch_any "Qwen/Qwen2-VL-2B-Instruct"
fetch_any "Qwen/Qwen2.5-VL-3B-Instruct"
fetch_any "Qwen/Qwen2.5-VL-7B-Instruct"
fetch_any "llava-hf/llava-1.5-7b-hf"
fetch_any "openai/clip-vit-base-patch32"
fetch_any "openai/clip-vit-large-patch14"
fetch_any "google/siglip-base-patch16-224"
fetch_any "facebook/dinov2-base"
fetch_any "chendelong/RemoteCLIP"

echo "== corpora sanity (all of these are required by the round) =="
for p in data/marine_captions/captions.json data/fathomnet8 data/NKSID/NKSID paper3/train-vqarad.parquet paper3/test-vqarad.parquet; do
  if [ -e "$BASE/$p" ]; then echo "   ok      $p"; else echo "   MISSING $p"; fi
done

echo
echo "SETUP_DONE - next:  bash cloud_next/run_all.sh phase1"
echo "Logs: $BASE/cloud_next/logs ; caches: $HF_HOME (keep both on the data disk)"