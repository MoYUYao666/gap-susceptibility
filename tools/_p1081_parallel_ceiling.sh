#!/usr/bin/env bash
# Decide whether the ~1 MB/s ceiling is per-connection or the host's link, before spending two hours on it.
#
# Measured so far: two parallel ModelScope shards, ~600 kB/s each, so ~1.2 MB/s aggregate. tuna reaches
# 3-4.5 MB/s on the same host, so either ModelScope is throttling or the link saturates at ~1 MB/s. This runs
# 16 parallel range requests on the SAME file while the background download continues, and reports the extra
# throughput that appears. If the aggregate does not rise, more connections will not help and the download
# should be abandoned rather than waited on.
set -uo pipefail
cd /root/p3
URL=https://modelscope.cn/models/llava-hf/llava-1.5-7b-hf/resolve/master/model-00002-of-00003.safetensors
OUT=/root/p3/_par
rm -rf "$OUT"; mkdir -p "$OUT"

echo "=== baseline: what the running download achieves on its own (10 s window) ==="
A1=$(du -sb /root/autodl-tmp/modelscope 2>/dev/null | cut -f1 || echo 0)
sleep 10
A2=$(du -sb /root/autodl-tmp/modelscope 2>/dev/null | cut -f1 || echo 0)
echo "  running download: $(( (A2-A1)/10/1000 )) KB/s"

echo "=== 16 extra parallel connections for 12 s ==="
for i in $(seq 1 16); do
  ( curl -sSL -m 12 -o "$OUT/p$i" -r $((i*20000000))-$((i*20000000+4000000)) "$URL" 2>/dev/null ) &
done
wait
EXTRA=$(du -sb "$OUT" 2>/dev/null | cut -f1 || echo 0)
echo "  16 connections fetched $((EXTRA/1000000)) MB in 12 s => $((EXTRA/12/1000)) KB/s extra"

echo "=== combined ==="
B1=$(du -sb /root/autodl-tmp/modelscope 2>/dev/null | cut -f1 || echo 0)
echo "  (the running download kept going during the test)"
rm -rf "$OUT"

echo "=== what the whole link can do, from the one source that is fast ==="
curl -sS -m 12 -o /dev/null -w '  tuna      : %{speed_download} B/s\n' https://pypi.tuna.tsinghua.edu.cn/simple/ 2>/dev/null || true
curl -sS -m 12 -o /dev/null -w '  modelscope: %{speed_download} B/s\n' "$URL" 2>/dev/null || true
echo PARALLEL_DONE
