#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Inspect the ModelScope COCO datasets to find the one that preserves the official id order.

The LLaVA sweep measured COCO val2014 ids in the annotation file's iteration order, so the recomputation needs
the same order. Two candidates were found: `modelscope/coco_2014_caption` (a loader script plus metadata) and
`AI-ModelScope/coco` (40 train parquet shards, 19.97 GB). This prints the loader script and the dataset
metadata so the right one can be chosen without guessing.

    python tools/_p1079_inspect_ms_coco.py   (runs on the host)
"""
from __future__ import annotations

import sys
from pathlib import Path

CACHE = Path("/root/autodl-tmp/modelscope")


def main() -> int:
    from modelscope import snapshot_download

    print("=== modelscope/coco_2014_caption (loader) ===")
    try:
        p = snapshot_download("modelscope/coco_2014_caption", cache_dir=str(CACHE))
        p = Path(p)
        for f in sorted(p.rglob("*")):
            if f.is_file():
                print(f"  {f.name}  {f.stat().st_size} bytes")
        script = next((f for f in p.rglob("*.py")), None)
        if script:
            text = script.read_text(encoding="utf-8", errors="replace")
            print("\n  --- loader script (first 90 lines) ---")
            for line in text.splitlines()[:90]:
                print("   " + line[:118])
        info = next((f for f in p.rglob("dataset_infos.json")), None)
        if info:
            print("\n  --- dataset_infos.json (first 600 chars) ---")
            print("   " + info.read_text(encoding="utf-8", errors="replace")[:600].replace("\n", "\n   "))
    except Exception as exc:
        print("  FAILED:", type(exc).__name__, str(exc)[:200])

    print("\n=== AI-ModelScope/coco (parquet) ===")
    try:
        from modelscope.hub.api import HubApi
        files = HubApi().get_dataset_files("AI-ModelScope/coco", recursive=True)
        for f in files[:12]:
            print(f"  {f.get('Path'):<64} {(f.get('Size') or 0)/1e6:>8.1f} MB")
        print(f"  ... {len(files)} files total")
    except Exception as exc:
        print("  FAILED:", type(exc).__name__, str(exc)[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
