#!/usr/bin/env bash
# Switch to the mirror method that worked on host 3, as the operator directed.
#
# Record from host 3 (2026-10-15), preserved in SUBMISSION/cloud_p3_setup.sh:
#   export HF_HOME=/root/autodl-tmp/hf
#   export HF_ENDPOINT=https://hf-mirror.com
#   python -c "from huggingface_hub import snapshot_download; snapshot_download('llava-hf/llava-1.5-7b-hf')"
#   -> 15 GB in about 6-8 minutes on that host's link.
#
# The ModelScope route reached 9.9 GB but its per-connection throttle left it crawling at 1-3 MB/s at the end,
# so the mirror is the better tool here. Nothing is deleted: ModelScope's partial download stays in place in
# case the mirror disappoints.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
export HF_HUB_DISABLE_PROGRESS_BARS=0
PY=/root/miniconda3/bin/python

echo "=== stop the ModelScope fetcher and the stalled COCO fetch ==="
pkill -9 -f _p1083_parallel_fetch || true
pkill -9 -f _p1088_coco_fixture || true
sleep 3
ps -eo pid,cmd | grep -E "_p1083|_p1088|curl" | grep -v grep || echo "  all stopped"

echo "=== mirror reachability (12 s) ==="
curl -sS -m 12 -o /dev/null -w '  hf-mirror config.json: %{http_code}  %{speed_download} B/s\n' \
  https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/config.json 2>/dev/null || echo "  unreachable"

echo "=== download the weights (background, as host 3 did) ==="
setsid bash -c "$PY - <<'PYEOF' > /root/p3/mirror_dl.log 2>&1
import os, time
from huggingface_hub import snapshot_download
t0 = time.time()
p = snapshot_download('llava-hf/llava-1.5-7b-hf', max_workers=8)
size = sum(os.path.getsize(os.path.join(r, f)) for r, _d, fs in os.walk(p) for f in fs)
dt = time.time() - t0
print('  path:', p)
print('  size %.2f GB in %.0f s (%.2f MB/s)' % (size/1e9, dt, size/1e6/max(dt,1)))
print('MIRROR_DL_DONE')
PYEOF" < /dev/null > /dev/null 2>&1 &
disown
sleep 45

echo "=== progress after 45 s ==="
du -sh /root/autodl-tmp/hf 2>/dev/null || echo "  0"
tail -4 /root/p3/mirror_dl.log 2>/dev/null | tr -d '\r' || echo "  no log yet"
echo "  (compare: ModelScope managed 1-16 MB/s; host 3's mirror run took 6-8 min for 15 GB)"
df -h /root/autodl-tmp | tail -1
echo MIRROR_STARTED
