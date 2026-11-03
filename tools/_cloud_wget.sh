
set -u
cd /root/autodl-tmp/work
M=https://hf-mirror.com
dl() {   # dl <repo> <file> <destdir>
  local repo="$1" file="$2" dest="$3"
  mkdir -p "$dest"
  if [ -s "$dest/$file" ]; then echo "SKIP $dest/$file"; return 0; fi
  echo "GET $repo/$file"
  wget -q --show-progress -c --tries=8 --timeout=30 \
       -O "$dest/$file" "$M/$repo/resolve/main/$file" \
    && echo "  OK $(stat -c%s "$dest/$file") B" || echo "  FAIL $repo/$file"
}
for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
         vocab.json merges.txt special_tokens_map.json model.safetensors; do
  dl openai/clip-vit-base-patch32 "$f" models/clip-vit-base-patch32
done
echo "=== b32 done ==="
for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
         vocab.json merges.txt special_tokens_map.json model.safetensors; do
  dl openai/clip-vit-base-patch16 "$f" models/clip-vit-base-patch16
done
echo "=== b16 done ==="
