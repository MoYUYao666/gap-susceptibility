#!/bin/bash
set -e
cd /root/autodl-tmp/a3
mkdir -p models
for f in RemoteCLIP-ViT-B-32.pt RemoteCLIP-ViT-L-14.pt; do
  src=$(find hf -name "$f" 2>/dev/null | head -1)
  if [ -n "$src" ]; then
    cp "$src" models/"$f"
    echo "copied $f"
  else
    echo "missing $f in cache"
  fi
done
ls -lh models
rm -rf hf
df -h /root/autodl-tmp | tail -1
