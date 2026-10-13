
set -u
cd /root/autodl-tmp/work
M=https://hf-mirror.com

# (1) kill everything cleanly (single-process iron rule)
for pat in _cloud_par _cloud_bin _cloud_redl _cloud_ms _cloud_wget; do
  pkill -f "$pat" 2>/dev/null || true
done
pkill -f "wget.*hf-mirror" 2>/dev/null || true
pkill -f "curl.*hf-mirror" 2>/dev/null || true
sleep 3
echo "cleaned; procs=$(pgrep -fc 'curl|wget' 2>/dev/null || echo 0)"

# (2) expected byte count: use a GET first byte + size_download following redirects (not HEAD)
expect() {
  curl -sL -o /dev/null --max-time 40 -w '%{size_download}' -r 0-0 "$1"
}

safe_dl() {  # safe_dl <url> <dest>
  url="$1"; dest="$2"; tmp="$dest.tmp"
  exp=$(expect "$url")
  echo "=== $dest"
  echo "  url: ${url:0:80}"
  echo "  curl-header-size: $exp"
  rm -f "$tmp"
  t0=$(date +%s)
  curl -sL --retry 8 --retry-delay 3 --max-time 3600 -o "$tmp" "$url"
  rc=$?
  sz=$(stat -c%s "$tmp" 2>/dev/null || echo 0)
  t1=$(date +%s)
  echo "  rc=$rc got=$sz in $((t1-t0))s ($(( sz/(t1-t0+1) )) B/s)"
  if [ "$sz" -lt 500000000 ]; then
    echo "  ❌ TOO SMALL — keeping the original file untouched"; rm -f "$tmp"; return 1
  fi
  mv -f "$tmp" "$dest"
  echo "  ✅ overwrote $dest ($sz B)"
  return 0
}

safe_dl "$M/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
        models/clip-vit-base-patch32/pytorch_model.bin
safe_dl "$M/openai/clip-vit-base-patch16/resolve/main/pytorch_model.bin" \
        models/clip-vit-base-patch16/pytorch_model.bin
echo SAFEDONE

# (3) verification
/root/miniconda3/bin/python - <<'PY'
import os
os.chdir("/root/autodl-tmp/work")
from transformers import CLIPModel
for d, want in [("models/clip-vit-base-patch32", 32), ("models/clip-vit-base-patch16", 16)]:
    try:
        m = CLIPModel.from_pretrained(d, local_files_only=True)
        print(f"  {d}: patch={m.config.vision_config.patch_size} "
              f"params={sum(p.numel() for p in m.parameters())/1e6:.1f}M "
              f"{'OK' if m.config.vision_config.patch_size == want else 'MISMATCH'}")
    except Exception as e:
        print(f"  {d}: LOAD FAIL {str(e)[:110]}")
PY
