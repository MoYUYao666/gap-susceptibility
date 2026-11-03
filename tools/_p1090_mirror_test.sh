#!/usr/bin/env bash
# Measure the mirror with one connection versus many, the same way the ModelScope route was measured.
#
# Host 3 pulled 15 GB from hf-mirror.com in 6-8 minutes, but this host managed only 125 MB in four minutes
# through `snapshot_download`. Either the mirror throttles a single connection here (which many connections
# would fix) or this host's route to it is genuinely slow (which they would not). The weights are a plain
# range-supporting resource, so the answer is one measurement.
set -uo pipefail
cd /root/p3
F=model-00001-of-00003.safetensors
URL=https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/$F
OUT=/root/p3/_mirrortest
rm -rf "$OUT"; mkdir -p "$OUT"

echo "=== single connection, 12 s ==="
curl -sSL -m 12 -o /dev/null -w '  1 conn: %{http_code}  %{speed_download} B/s\n' "$URL" 2>/dev/null || echo "  1 conn failed"

echo "=== 16 connections, 12 s ==="
for i in $(seq 1 16); do
  ( curl -sSL -m 12 -o "$OUT/p$i" -r $((i*30000000))-$((i*30000000+6000000)) "$URL" 2>/dev/null ) &
done
wait
GOT=$(du -sb "$OUT" | cut -f1)
echo "  16 conns fetched $((GOT/1000000)) MB in 12 s => $((GOT/12/1000)) KB/s aggregate"
rm -rf "$OUT"

echo "=== how far has snapshot_download got, and is it still moving? ==="
A=$(du -sb /root/autodl-tmp/hf 2>/dev/null | cut -f1)
sleep 20
B=$(du -sb /root/autodl-tmp/hf 2>/dev/null | cut -f1)
echo "  HF cache: $((A/1000000)) MB -> $((B/1000000)) MB  ($(( (B-A)/20/1000 )) KB/s)"
ls -la /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/blobs/ 2>/dev/null | tail -6
echo "=== for comparison, what ModelScope's partial download holds ==="
du -sh /root/autodl-tmp/modelscope 2>/dev/null
df -h /root/autodl-tmp | tail -1
echo MIRROR_TEST_DONE
