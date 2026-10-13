
set -u
cd /root/autodl-tmp/work
M=https://hf-mirror.com

# ① Kill every download cleanly to avoid concurrent writes
pkill -f _cloud_par 2>/dev/null || true
pkill -f _cloud_bin 2>/dev/null || true
pkill -f "wget.*hf-mirror" 2>/dev/null || true
pkill -f "curl.*hf-mirror" 2>/dev/null || true
sleep 3

# ② Remove corrupted / incomplete files
rm -f models/*/model.safetensors models/*/*.incomplete models/*/*.p[0-9]* \
      models/*/*.part* 2>/dev/null || true
find models -name "pytorch_model.bin" -size -100M -delete 2>/dev/null || true
echo "cleaned: $(ls models/clip-vit-base-patch32/ | tr '\n' ' ')"

# ③ Serial download + immediate verification
dl_one() {  # dl_one <repo> <file> <dest>
  repo="$1"; file="$2"; dest="$3"
  url="$M/$repo/resolve/main/$file"
  echo "=== DL $dest ==="
  total=$(curl -sIL "$url" | awk 'BEGIN{IGNORECASE=1}/^content-length:/{v=$2}END{print v}' | tr -d '\r')
  echo "  expect total=$total"
  PAR=16; chunk=$(( total / PAR + 1 )); pids=""; t0=$(date +%s)
  for i in $(seq 0 $((PAR-1))); do
    a=$(( i * chunk )); b=$(( a + chunk - 1 ))
    [ "$b" -ge "$total" ] && b=$(( total - 1 ))
    curl -sL --retry 6 --retry-delay 2 -r "${a}-${b}" -o "${dest}.p${i}" "$url" &
    pids="$pids $!"
  done
  for p in $pids; do wait $p; done
  cat "${dest}".p* > "$dest" && rm -f "${dest}".p*
  sz=$(stat -c%s "$dest" 2>/dev/null || echo 0)
  t1=$(date +%s)
  echo "  got $sz / $total in $((t1-t0))s ($(( sz/(t1-t0+1) )) B/s)"
  if [ "$sz" != "$total" ]; then echo "  SIZE MISMATCH"; return 1; fi
  return 0
}

REPO32=openai/clip-vit-base-patch32
REPO16=openai/clip-vit-base-patch16
dl_one "$REPO32" pytorch_model.bin models/clip-vit-base-patch32/pytorch_model.bin
dl_one "$REPO16" pytorch_model.bin models/clip-vit-base-patch16/pytorch_model.bin
echo DLDONE
