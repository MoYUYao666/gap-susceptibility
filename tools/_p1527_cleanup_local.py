# -*- coding: utf-8 -*-
r"""Remove large, reproducible leftovers from the local workspace.

    python tools/_p1527_cleanup_local.py [--apply]

Targets (all re-downloadable or redundant):
  * models/llava-hf/.git           (LFS object copies of the same weights; ~14 GB)
  * models/_modelscope_cache       (duplicate of models/clip-vit-large-patch14; ~6.9 GB)
  * duplicate weight formats where model.safetensors exists (pytorch_model.bin / tf_model.h5 / flax)
  * models/Qwen2-VL-2B-Instruct and models/Qwen2.5-VL-3B-Instruct (results archived; re-downloadable)
  * data/dtd/dtd-r1.0.1.tar.gz if the extracted directory exists
  * cloud_upload/ and cloud_upload.zip staging leftovers
"""
from __future__ import annotations

import argparse
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dir_size(p):
    t = 0
    for r, _, f in os.walk(p):
        for x in f:
            try:
                t += os.path.getsize(os.path.join(r, x))
            except OSError:
                pass
    return t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    targets = []
    targets.append(("models/llava-hf/.git", "LFS duplicate copy of the weights"))
    targets.append(("models/_modelscope_cache", "duplicate of models/clip-vit-large-patch14"))
    for rel in ("models/clip-vit-large-patch14/tf_model.h5", "models/clip-vit-large-patch14/pytorch_model.bin",
                "models/clip-vit-large-patch14/flax_model.msgpack",
                "models/clip-vit-base-patch32/tf_model.h5", "models/clip-vit-base-patch32/pytorch_model.bin",
                "models/clip-vit-base-patch32/flax_model.msgpack",
                "models/blip-caption-base/tf_model.h5",
                "models/openclip/pytorch_model.bin", "models/openclip/open_clip_pytorch_model.bin",
                "models/openclip/.cache",
                "models/siglip-base-patch16-224/pytorch_model.bin",
                "models/dinov2-base/pytorch_model.bin",
                "models/Qwen2-VL-2B-Instruct", "models/Qwen2.5-VL-3B-Instruct",
                "data/dtd/dtd-r1.0.1.tar.gz",
                "cloud_upload", "cloud_upload.zip"):
        targets.append((rel, "redundant/reproducible"))
    total = 0
    for rel, why in targets:
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            print(f"  skip (missing) {rel}")
            continue
        s = dir_size(p) if os.path.isdir(p) else os.path.getsize(p)
        total += s
        print(f"  {s/1e9:7.2f} GB  {rel:55s} {why}")
    print(f"  total to free: {total/1e9:.2f} GB")
    if a.apply:
        for rel, _ in targets:
            p = os.path.join(REPO, rel)
            if not os.path.exists(p):
                continue
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
        print("  deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
