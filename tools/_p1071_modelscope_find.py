#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Find which ModelScope repositories actually exist, by asking the client to fetch them.

The REST endpoints returned 404/500, so the client's own dataset and model listing is used instead. For each
candidate this reports whether it exists and how large it is, without committing to a full download.

    python tools/_p1071_modelscope_find.py   (runs on the host)
"""
from __future__ import annotations

import sys


def main() -> int:
    from modelscope.hub.api import HubApi
    from modelscope.msdatasets import MsDataset

    api = HubApi()

    # 1. LLaVA weights
    print("=== model candidates ===")
    for repo in ("AI-ModelScope/llava-1.5-7b-hf", "llava-hf/llava-1.5-7b-hf",
                 "AI-ModelScope/llava-v1.6-vicuna-7b", "Qwen/Qwen2-VL-2B-Instruct"):
        try:
            files = api.get_model_files(repo, recursive=True)
            total = sum(f.get("Size", 0) or 0 for f in files)
            print(f"  OK   {repo:<40} {len(files)} files, {total / 1e9:.2f} GB")
        except Exception as exc:
            print(f"  FAIL {repo:<40} {type(exc).__name__}: {str(exc)[:70]}")

    # 2. COCO annotation material
    print("\n=== dataset candidates ===")
    for repo in ("modelscope/coco_2014_caption", "AI-ModelScope/coco_2014_caption",
                 "modelscope/coco-2014", "swift/coco_2014_caption"):
        try:
            files = api.get_dataset_files(repo, recursive=True)
            names = [f.get("Path", "?") for f in files]
            total = sum(f.get("Size", 0) or 0 for f in files)
            print(f"  OK   {repo:<40} {len(files)} files, {total / 1e9:.2f} GB")
            for n in names[:8]:
                print(f"         {n}")
        except Exception as exc:
            print(f"  FAIL {repo:<40} {type(exc).__name__}: {str(exc)[:70]}")

    # 3. what the listing call looks like for a known-good dataset
    print("\n=== probe the client's dataset listing for 'coco' ===")
    try:
        ds = MsDataset.load("modelscope/coco_2014_caption", split="validation", download_mode="force_redownload")
        print("  loaded:", ds)
    except Exception as exc:
        print(f"  load failed: {type(exc).__name__}: {str(exc)[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
