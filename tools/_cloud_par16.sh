
set -u
cd /root/autodl-tmp/work
M=https://hf-mirror.com
PAR=16

pdl() {  # pdl <url> <dest>
  url="$1"; dest="$2"
  if [ -s "$dest" ]; then
    sz=$(stat -c%s "$dest")
    if [ "$sz" -gt 100000000 ]; then echo "SKIP $dest ($sz B)"; return 0; fi
  fi
  mkdir -p "$(dirname "$dest")"
  total=$(curl -sIL "$url" | awk 'BEGIN{IGNORECASE=1}/^content-length:/{v=$2}END{print v}' | tr -d '\r')
  if [ -z "${total:-}" ] || [ "${total:-0}" -lt 1000000 ]; then
    echo "NOLEN $url"; curl -sL -o "$dest" "$url"; return $?
  fi
  echo "DL $dest  total=$total  x$PAR"
  t0=$(date +%s)
  chunk=$(( total / PAR + 1 ))
  pids=""
  for i in $(seq 0 $((PAR-1))); do
    a=$(( i * chunk )); b=$(( a + chunk - 1 ))
    [ "$b" -ge "$total" ] && b=$(( total - 1 ))
    curl -sL --retry 5 --retry-delay 2 -r "${a}-${b}" -o "${dest}.p${i}" "$url" &
    pids="$pids $!"
  done
  for p in $pids; do wait $p; done
  cat "${dest}".p* > "$dest" && rm -f "${dest}".p*
  t1=$(date +%s)
  sz=$(stat -c%s "$dest")
  echo "  OK $sz B in $((t1-t0))s  → $(( sz / (t1-t0+1) )) B/s"
}

# Fetch small files first (faster)
for repo_dir in "openai/clip-vit-base-patch32:models/clip-vit-base-patch32" \
                "openai/clip-vit-base-patch16:models/clip-vit-base-patch16"; do
  repo="${repo_dir%%:*}"; d="${repo_dir##*:}"
  for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
           vocab.json merges.txt special_tokens_map.json; do
    [ -s "$d/$f" ] || curl -sL -o "$d/$f" "$M/$repo/resolve/main/$f"
  done
  echo "small files done: $d"
done

pdl "$M/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
    models/clip-vit-base-patch32/pytorch_model.bin
echo "=== b32 done ==="
pdl "$M/openai/clip-vit-base-patch16/resolve/main/pytorch_model.bin" \
    models/clip-vit-base-patch16/pytorch_model.bin
echo "=== b16 done ==="
