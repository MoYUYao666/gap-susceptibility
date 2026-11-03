#!/usr/bin/env bash
# Find a source that can actually deliver the COCO material, by measuring throughput rather than guessing.
#
# Measured 2026-10-16: images.cocodataset.org delivered about 1.5 KB/s to this host (3.6 MB of the 472 MB
# annotation archive in 40 minutes), which would take days. This probes the alternatives -- the HuggingFace
# mirror the host already uses for weights, and a couple of annotation mirrors -- and reports bytes per second
# for each, so the source is chosen on evidence.
set -uo pipefail
cd /root/p3
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
PY=/root/miniconda3/bin/python

probe() {  # label, url, seconds
  local label="$1" url="$2" secs="${3:-12}"
  local out
  out=$(curl -sS -m "$secs" -o /dev/null -w '%{size_download} %{speed_download}' "$url" 2>/dev/null || echo "0 0")
  local bytes=$(echo "$out" | awk '{print $1}')
  local speed=$(echo "$out" | awk '{print $2}')
  printf '  %-46s %10.0f B/s  (%s bytes in %ss)\n' "$label" "${speed:-0}" "${bytes:-0}" "$secs"
}

echo "=== throughput probe (12 s each) ==="
probe "images.cocodataset.org (annotations zip)" "http://images.cocodataset.org/annotations/annotations_trainval2014.zip"
probe "images.cocodataset.org (one image)"      "http://images.cocodataset.org/val2014/COCO_val2014_000000000139.jpg"
probe "hf-mirror.com (llava config.json)"       "https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/config.json"
probe "hf-mirror.com (coco annotations repo)"   "https://hf-mirror.com/datasets/hf-internal-testing/coco_captions/resolve/main/README.md"
probe "github raw (COCO val2014 captions)"      "https://raw.githubusercontent.com/tylin/coco-caption/master/annotations/captions_val2014.json"

echo
echo "=== what the host can reach for datasets ==="
$PY - <<'PYEOF'
import json, urllib.request
for name, url in (
    ("hf datasets list (mirror)", "https://hf-mirror.com/api/datasets?search=coco&limit=5"),
    ("modelscope api", "https://www.modelscope.cn/api/v1/datasets?Name=coco&PageSize=5"),
):
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        if isinstance(data, list):
            print(f"  {name}: {[d.get('id') or d.get('Name') for d in data][:5]}")
        else:
            print(f"  {name}: keys={list(data)[:5]}")
    except Exception as exc:
        print(f"  {name}: FAILED {type(exc).__name__}")
PYEOF
echo THROUGHPUT_DONE
