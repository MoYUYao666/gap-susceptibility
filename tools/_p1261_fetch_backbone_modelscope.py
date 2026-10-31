# -*- coding: utf-8 -*-
r"""Download a fourth vision--language backbone from ModelScope (hf-mirror and huggingface.co are unreachable here).

The repository rule is: probe first, then pick the source by measured throughput. On this machine hf-mirror and
huggingface.co time out and modelscope.cn answers, so the download goes through ModelScope, weights straight to
`models/` (never local-then-upload).

    python tools/_p1261_fetch_backbone_modelscope.py --repo openai-mirror/clip-vit-large-patch14 --target models/clip-vit-large-patch14
"""
from __future__ import annotations

import argparse
import os
import shutil
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="openai-mirror/clip-vit-large-patch14")
    ap.add_argument("--target", default="models/clip-vit-large-patch14")
    a = ap.parse_args()
    from modelscope.hub.snapshot_download import snapshot_download

    target = os.path.join(REPO, a.target)
    if os.path.isdir(target) and any(f.endswith((".bin", ".safetensors")) for f in os.listdir(target)):
        print("  already present:", os.path.relpath(target, REPO), flush=True)
        return 0
    t0 = time.time()
    cache = os.path.join(REPO, "models", "_modelscope_cache")
    path = snapshot_download(a.repo, cache_dir=cache)
    print("  downloaded to", path, "in %.1f s" % (time.time() - t0), flush=True)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(path, target, dirs_exist_ok=True)
    size = sum(os.path.getsize(os.path.join(target, f)) for f in os.listdir(target)
               if os.path.isfile(os.path.join(target, f)))
    print("  installed %s (%.2f GB)" % (os.path.relpath(target, REPO), size / 1024 ** 3), flush=True)
    for f in sorted(os.listdir(target)):
        print("   ", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
