#!/usr/bin/env bash
# Decide whether the slow weight download is a per-connection limit or the host's total bandwidth.
#
# ModelScope is delivering about 633 kB/s for a 4.96 GB shard, which would take hours. If the host has spare
# aggregate bandwidth, several parallel connections fix it; if the link is saturated, they will not and the
# approach has to change. Eight concurrent fetches of a real shard's first megabytes measure exactly that.
set -uo pipefail
cd /root/p3
BASE=https://modelscope.cn/models/llava-hf/llava-1.5-7b-hf/resolve/master
OUT=/root/p3/_bwtest
rm -rf "$OUT"; mkdir -p "$OUT"

echo "=== single connection (10 s) ==="
curl -sS -m 10 -o /dev/null -w '  1 conn : %{speed_download} B/s\n' \
  "$BASE/model-00001-of-00003.safetensors" 2>/dev/null || echo "  1 conn : failed"

echo "=== eight connections (10 s each, summed) ==="
for i in $(seq 1 8); do
  ( curl -sS -m 10 -o "$OUT/p$i" -r 0-8000000 "$BASE/model-00001-of-00003.safetensors" 2>/dev/null ) &
done
wait
TOT=$(du -sb "$OUT" 2>/dev/null | cut -f1)
echo "  total fetched in 10 s: $((TOT/1000000)) MB  => $((TOT/10/1000)) KB/s aggregate"

echo "=== tools available for parallel download ==="
for t in aria2c wget axel hf; do command -v $t >/dev/null && echo "  $t: yes" || echo "  $t: no"; done

echo "=== other candidate sources for the same weights ==="
curl -sS -m 12 -o /dev/null -w '  hf-mirror resolve : %{http_code} %{speed_download} B/s\n' \
  "https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/model-00001-of-00003.safetensors" 2>/dev/null || echo "  hf-mirror failed"
curl -sS -m 12 -o /dev/null -w '  modelscope resolve: %{http_code} %{speed_download} B/s\n' \
  "$BASE/model-00001-of-00003.safetensors" 2>/dev/null || echo "  modelscope failed"
rm -rf "$OUT"
echo BW_DONE
