
set -u
cd /root/autodl-tmp/work
M=https://hf-mirror.com

get() {  # get <repo> <file> <destdir> [newname]
  repo="$1"; file="$2"; dest="$3"; newname="${4:-$file}"
  mkdir -p "$dest"
  if [ -s "$dest/$newname" ]; then echo "SKIP $dest/$newname"; return 0; fi
  rm -f "$dest/$newname"
  echo "GET $repo/$file"
  wget -q -c --tries=10 --timeout=40 --waitretry=5 \
       -O "$dest/$newname" "$M/$repo/resolve/main/$file"
  rc=$?
  if [ $rc -eq 0 ] && [ -s "$dest/$newname" ]; then
    echo "  OK $(stat -c%s "$dest/$newname") B"
  else
    echo "  FAIL($rc) $repo/$file"; rm -f "$dest/$newname"
  fi
}

# ── CLIP ViT-B/32 ──
for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
         vocab.json merges.txt special_tokens_map.json pytorch_model.bin; do
  get openai/clip-vit-base-patch32 "$f" models/clip-vit-base-patch32
done
echo "=== b32 done ==="

# ── CLIP ViT-B/16 ──
for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
         vocab.json merges.txt special_tokens_map.json pytorch_model.bin; do
  get openai/clip-vit-base-patch16 "$f" models/clip-vit-base-patch16
done
echo "=== b16 done ==="

# ── OpenCLIP ViT-B/32 (laion2B) ──
OC=laion/CLIP-ViT-B-32-laion2B-s34B-b79K
for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
         vocab.json merges.txt special_tokens_map.json; do
  get "$OC" "$f" models/openclip
done
get "$OC" open_clip_pytorch_model.bin models/openclip
get "$OC" open_clip_config.json models/openclip
echo "=== openclip done ==="
rm -f models/*/model.safetensors
echo ALLDONE
