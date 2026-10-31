# -*- coding: utf-8 -*-
r"""Fetch the three backbones used by the A3 cloud supplements.

RemoteCLIP ViT-B/32 and ViT-L/14, GeoRSCLIP ViT-B/32 (for the optional GeoRSCLIP-L/14 phase the checkpoint is listed
but downloaded lazily). Uses the mirror by default; the environment variable HF_ENDPOINT should point at it.

Usage
  python fetch_weights.py [--geol14]
"""
import argparse
import os
import shutil
import sys
import time

from huggingface_hub import hf_hub_download

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models")


def fetch(repo, filename, dest):
    os.makedirs(MODELS, exist_ok=True)
    out = os.path.join(MODELS, dest)
    if os.path.exists(out) and os.path.getsize(out) > 1e8:
        print("have", dest, "%.0f MB" % (os.path.getsize(out) / 1e6))
        return out
    t0 = time.time()
    path = hf_hub_download(repo_id=repo, filename=filename, cache_dir=os.environ.get("HF_HOME"))
    shutil.copy(path, out)
    print("fetched %-28s -> %s (%.0f MB, %.0f s)" % (filename, dest, os.path.getsize(out) / 1e6, time.time() - t0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geol14", action="store_true")
    args = ap.parse_args()
    fetch("chendelong/RemoteCLIP", "RemoteCLIP-ViT-B-32.pt", "RemoteCLIP-ViT-B-32.pt")
    fetch("chendelong/RemoteCLIP", "RemoteCLIP-ViT-L-14.pt", "RemoteCLIP-ViT-L-14.pt")
    fetch("BiliSakura/GeoRSCLIP-ViT-B-32", "GeoRSCLIP-ViT-B-32.pt", "GeoRSCLIP-ViT-B-32.pt")
    if args.geol14:
        fetch("BiliSakura/GeoRSCLIP-ViT-L-14", "GeoRSCLIP-ViT-L-14.pt", "GeoRSCLIP-ViT-L-14.pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
