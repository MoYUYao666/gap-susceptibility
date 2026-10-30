#!/usr/bin/env bash
# Two questions, one pass: does parallelism beat the 633 kB/s per-connection limit, and does ModelScope carry
# the COCO captions? No HuggingFace is used (project rule).
set -uo pipefail
export PYTHONIOENCODING=utf-8
cd /root/p3
BASE=https://modelscope.cn/models/llava-hf/llava-1.5-7b-hf/resolve/master
OUT=/root/p3/_bwtest
rm -rf "$OUT"; mkdir -p "$OUT"

echo "=== aggregate bandwidth: 8 parallel range requests, 12 s ==="
for i in $(seq 1 8); do
  ( curl -sS -m 12 -o "$OUT/p$i" -r 100000000-140000000 "$BASE/model-00001-of-00003.safetensors" 2>/dev/null ) &
done
wait
TOT=$(du -sb "$OUT" 2>/dev/null | cut -f1 || echo 0)
echo "  fetched $((TOT/1000000)) MB in 12 s => $((TOT/12/1000)) KB/s aggregate (8 connections)"
rm -rf "$OUT"

echo "=== ModelScope dataset candidates for COCO captions ==="
/root/miniconda3/bin/python - <<'PYEOF'
from modelscope.hub.api import HubApi
api = HubApi()
cands = [
    "modelscope/coco_2014_caption",
    "AI-ModelScope/coco_2014_caption",
    "modelscope/coco-2014",
    "modelscope/coco2014",
    "AI-ModelScope/coco",
    "modelscope/mscoco",
    "swift/coco_2014_caption",
    "iic/coco_2014_caption",
]
for repo in cands:
    try:
        files = api.get_dataset_files(repo, recursive=True)
        total = sum((f.get("Size") or 0) for f in files)
        print(f"  OK   {repo:<34} {len(files)} files {total/1e9:.2f} GB")
        for f in files[:6]:
            print(f"         {f.get('Path')}")
    except Exception as exc:
        print(f"  FAIL {repo:<34} {type(exc).__name__}: {str(exc)[:56]}")
PYEOF

echo "=== current model download progress ==="
du -sh /root/autodl-tmp/modelscope 2>/dev/null
tail -2 /root/p3/ms_llava_dl.log 2>/dev/null | tr '\r' '\n' | tail -3
echo BW_AND_MS_DONE
