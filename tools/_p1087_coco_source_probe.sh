#!/usr/bin/env bash
# Two things the recomputation still needs, both probed at once:
#   1. a source for the COCO val2014 captions that is usable from this host (the official archive crawls at
#      about 400 B/s single-connection, exactly like ModelScope's weights did, so multi-connection may fix it);
#   2. whatever the ModelScope COCO datasets actually expose, queried through the right endpoint
#      (`get_dataset_files`, not `get_model_files` -- the first probe used the wrong one and got a 404).
set -uo pipefail
cd /root/p3
PY=/root/miniconda3/bin/python

echo "=== multi-connection attempt on the official COCO annotations (8 connections, 20 s) ==="
URL=http://images.cocodataset.org/annotations/annotations_trainval2014.zip
SZ=$(curl -sSI -m 20 "$URL" | tr -d '\r' | awk '/[Cc]ontent-[Ll]ength/ {print $2}')
echo "  archive size: ${SZ:-unknown} bytes"
if [ -n "${SZ:-}" ]; then
  OUT=/root/p3/_cocotest; rm -rf "$OUT"; mkdir -p "$OUT"
  for i in $(seq 0 7); do
    a=$(( i * SZ / 8 )); b=$(( (i+1) * SZ / 8 - 1 ))
    ( curl -sS -m 20 -o "$OUT/p$i" -r "$a-$b" "$URL" 2>/dev/null ) &
  done
  wait
  GOT=$(du -sb "$OUT" | cut -f1)
  echo "  8 connections fetched $((GOT/1000000)) MB in 20 s => $((GOT/20/1000)) KB/s"
  rm -rf "$OUT"
fi

echo
echo "=== ModelScope COCO datasets, via the dataset endpoint ==="
$PY - <<'PYEOF'
from modelscope.hub.api import HubApi
api = HubApi()
for repo in ("modelscope/coco_2014_caption", "AI-ModelScope/coco", "modelscope/coco_2014_caption_test",
             "AI-ModelScope/coco_2014_caption"):
    try:
        files = api.get_dataset_files(repo, recursive=True)
        print(f"  OK   {repo:<34} {len(files)} files")
        for f in files[:8]:
            print(f"        {f.get('Path'):<64} {(f.get('Size') or 0)/1e6:>8.1f} MB")
    except Exception as exc:
        print(f"  FAIL {repo:<34} {type(exc).__name__}: {str(exc)[:52]}")
PYEOF

echo
echo "=== multi-connection fetch still healthy? ==="
tail -2 /root/p3/mtdl.log 2>/dev/null | tr -d '\r'
echo COCO_PROBE_DONE
