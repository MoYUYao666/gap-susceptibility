# -*- coding: utf-8 -*-
r"""Inventory the local datasets to choose a larger one for the R2-3 validation.

The reviewer asks for validation on a larger dataset. data/ holds 119,747 images (55.7 GB), so it
may already contain something larger than Flickr30k (31k) and COCO (123k total, but the retrieval
split used is much smaller). This identifies what is actually on disk and whether it is usable.

    python tools/_p748_dataset_inventory.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for name in ("data", "coco", "flickr30k"):
        d = REPO / name
        if not d.exists():
            print(f"  {name}/ absent")
            continue
        print("=" * 106)
        print(f"{name}/")
        print("=" * 106)
        subs = [p for p in d.iterdir() if p.is_dir()]
        print(f"  {len(subs)} subdirectories")
        for s in sorted(subs, key=lambda p: -sum(1 for _ in p.rglob("*") if _.is_file()))[:14]:
            files = [f for f in s.rglob("*") if f.is_file()]
            imgs = [f for f in files if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
            sz = sum(f.stat().st_size for f in files) / 1024 / 1024
            print(f"     {s.name:<44} {len(imgs):>7} img  {len(files):>7} files {sz:>9.1f} MB")
            # a sample of the file-name shapes
            sample = [f.name for f in imgs[:2]]
            if sample:
                print(f"        e.g. {sample}")
        ann = [f for f in d.rglob("*") if f.suffix.lower() in (".json", ".csv", ".tsv", ".txt")]
        print(f"  {len(ann)} annotation-ish files")
        for f in ann[:10]:
            print(f"     {f.relative_to(REPO)}  ({f.stat().st_size:,} bytes)")
        print()

    print("=" * 106)
    print("what src/dataset.py expects")
    print("=" * 106)
    p = REPO / "src" / "dataset.py"
    if p.exists():
        t = p.read_text(encoding="utf-8", errors="ignore")
        print(f"  {len(t.splitlines())} lines")
        for m in re.finditer(r".{0,100}(flickr30k|coco|dataset_name|root|split|\.json|\.csv)"
                             r".{0,140}", t):
            seg = " ".join(m.group(0).split())
            print(f"     {seg[:210]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
