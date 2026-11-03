# -*- coding: utf-8 -*-
r"""云端：用正确的文件名下载 CLIP 权重（**OpenAI 仓库只有 `pytorch_model.bin`**）（2026-10-09）。

## 上一版失败原因（实测）

```
models/clip-vit-base-patch32/model.safetensors   0 B   ← 下成了空文件
models/clip-vit-base-patch16/model.safetensors   0 B
```

**OpenAI 的 CLIP 仓库没有 `.safetensors`**，权重是 **`pytorch_model.bin`**（约 605 MB / 605 MB）。
**→ 改下 `.bin`；openclip 用 `open_clip_pytorch_model.bin`。**

**下载后强制校验**：逐个 `CLIPModel.from_pretrained(local_files_only=True)` 并断言 patch size。

    $env:CLOUD_PW='...'; python tools\_cloud_models_bin.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

SH = r'''
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
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== 上传并后台下载（正确文件名）===")
        local = REPO / "tools" / "_cloud_bin.sh"
        io.open(local, "w", encoding="utf-8", newline="\n").write(SH)
        sftp = c.open_sftp()
        sftp.put(str(local), f"{WORK}/_cloud_bin.sh")
        sftp.close()
        run(c, f"cd {WORK} && sed -i 's/\\r$//' _cloud_bin.sh && "
               f"nohup bash _cloud_bin.sh > outputs_bin.log 2>&1 & echo started")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
