#!/usr/bin/env bash
# Morning probe: what the new host is, and how fast each source is from here.
#
# The rule requires measuring before choosing a source, because two hosts on the same day differed by 60x on the
# mirror (host 3: 30-40 MB/s; another instance: 0.5 MB/s). Twelve seconds per source settles it.
set -uo pipefail
echo "=== host ==="
hostname; date '+%Y-%m-%d %H:%M:%S %Z'
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
nproc; free -g | head -2
df -h / /root/autodl-tmp 2>/dev/null | tail -2

echo "=== python ==="
ls -d /root/miniconda3 2>/dev/null && /root/miniconda3/bin/python -V || echo "no conda"
/root/miniconda3/bin/python -c "import torch, torchvision; print('  torch', torch.__version__, '| torchvision', torchvision.__version__)" 2>/dev/null || echo "  torch/torchvision missing"

echo "=== source throughput, 12 s each ==="
probe() { local label="$1" url="$2"
  local r; r=$(curl -sS -m 12 -o /dev/null -w '%{http_code} %{speed_download}' "$url" 2>/dev/null || echo "ERR 0")
  printf '  %-34s %s\n' "$label" "$r"; }
probe "hf-mirror config.json"        "https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/config.json"
probe "hf-mirror 100MB shard range"  "https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/model-00001-of-00003.safetensors"
probe "modelscope resolve"           "https://modelscope.cn/models/llava-hf/llava-1.5-7b-hf/resolve/master/config.json"
probe "tuna pypi"                    "https://pypi.tuna.tsinghua.edu.cn/simple/"
probe "coco image"                   "http://images.cocodataset.org/val2014/COCO_val2014_000000000139.jpg"

echo "=== mirror with 16 connections, 12 s (the per-connection test) ==="
OUT=/root/_bw; rm -rf "$OUT"; mkdir -p "$OUT"
URL=https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/model-00001-of-00003.safetensors
for i in $(seq 1 16); do
  ( curl -sSL -m 12 -o "$OUT/p$i" -r $((i*30000000))-$((i*30000000+6000000)) "$URL" 2>/dev/null ) &
done
wait
GOT=$(du -sb "$OUT" 2>/dev/null | cut -f1 || echo 0)
echo "  16 conns fetched $((GOT/1000000)) MB in 12 s => $((GOT/12/1000)) KB/s aggregate"
rm -rf "$OUT"
echo PROBE_DONE
