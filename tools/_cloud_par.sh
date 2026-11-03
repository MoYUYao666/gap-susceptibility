
set -u
cd /root/autodl-tmp/work
M=https://hf-mirror.com
PAR=8

# 测带宽
echo "=== 带宽探测（1 秒取 5MB）==="
curl -s -o /dev/null -w '  speed: %{speed_download} B/s\n' --max-time 6 \
  -r 0-5000000 "$M/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" || true

# 装 aria2（若能）
if ! command -v aria2c >/dev/null 2>&1; then
  (apt-get install -y -q aria2 >/dev/null 2>&1 || pip install -q aria2p >/dev/null 2>&1) || true
fi

pdl() {  # pdl <url> <dest>
  url="$1"; dest="$2"
  if [ -s "$dest" ]; then echo "SKIP $dest"; return 0; fi
  if command -v aria2c >/dev/null 2>&1; then
    echo "aria2c x$PAR -> $dest"
    aria2c -q -x $PAR -s $PAR -k 4M --file-allocation=none \
           --max-tries=10 --retry-wait=3 -d "$(dirname "$dest")" \
           -o "$(basename "$dest")" "$url" && echo "  OK $(stat -c%s "$dest")"
    return $?
  fi
  # curl 分段并行
  total=$(curl -sI -L "$url" | awk 'BEGIN{IGNORECASE=1}/content-length/{print $2}' | tr -d '\r' | tail -1)
  if [ -z "$total" ] || [ "$total" -lt 1000000 ] 2>/dev/null; then
    echo "no size -> single curl"; curl -sL -C - -o "$dest" "$url"; return $?
  fi
  echo "curl x$PAR segments -> $dest (total $total)"
  chunk=$(( total / PAR + 1 ))
  pids=""
  for i in $(seq 0 $((PAR-1))); do
    a=$(( i * chunk )); b=$(( a + chunk - 1 ))
    [ "$b" -ge "$total" ] && b=$(( total - 1 ))
    curl -sL -r "${a}-${b}" -o "${dest}.part${i}" "$url" &
    pids="$pids $!"
  done
  for p in $pids; do wait $p; done
  cat "${dest}".part* > "$dest" && rm -f "${dest}".part*
  echo "  OK $(stat -c%s "$dest") / $total"
}

pdl "$M/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
    models/clip-vit-base-patch32/pytorch_model.bin
echo "=== b32 weights done ==="
pdl "$M/openai/clip-vit-base-patch16/resolve/main/pytorch_model.bin" \
    models/clip-vit-base-patch16/pytorch_model.bin
echo "=== b16 weights done ==="
OC=laion/CLIP-ViT-B-32-laion2B-s34B-b79K
pdl "$M/$OC/resolve/main/open_clip_pytorch_model.bin" \
    models/openclip/open_clip_pytorch_model.bin
echo "=== openclip weights done ==="

# 清掉 0 字节的 safetensors
find models -name "model.safetensors" -size 0 -delete 2>/dev/null
echo ALLWEIGHTDONE
