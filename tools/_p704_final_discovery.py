# -*- coding: utf-8 -*-
r"""Last discovery pass, then the ledger can be written.

1. Print the structure of pr_stats_hardened.json around its primary estimate, to see whether the
   slope / SE / p the paper quotes have a named field.
2. Count the actual experiments in each archive family, so the paper's n = 383, n = 221, 117
   mechanism runs and 95 strict-freezing controls can be sourced by counting rather than by name.
3. Check coco_ode_table.json for the per-fit values behind the paper's alpha statistics.

    python tools/_p704_final_discovery.py [--apply]
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
PUB = REPO / "publish_clean"


def walk(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 104)
    print("1. pr_stats_hardened.json: keys, and anything named like a primary estimate")
    print("=" * 104)
    p = PUB / "outputs/analysis/pr_stats_hardened.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        print(f"  top-level: {list(d.keys()) if isinstance(d, dict) else type(d)}")
        for path, v in walk(d):
            key = path.split(".")[-1].split("[")[0]
            if re.search(r"slope|se\b|stderr|standard_error|p_|pval|ci|n_obs|n$|r2",
                         key, re.I) and not re.search(r"folds\[\d+\]", path):
                print(f"     {path} = {v}")
    print()

    print("=" * 104)
    print("2. archive families: how many runs are actually there")
    print("=" * 104)
    fams = {
        "strict_freeze*": "outputs/strict_freeze",
        "strict_freeze_bioclip": "outputs/strict_freeze_bioclip",
        "strict_freeze_openclip": "outputs/strict_freeze_openclip",
        "coco_sweep": "outputs/coco_sweep",
        "coco_sweep_text_only": "outputs/coco_sweep_text_only",
        "vlm_seeds_bf16": "outputs/vlm_seeds_bf16",
        "flickr30k_seeds": "outputs/flickr30k_seeds",
        "siglip_strict": "outputs/siglip_strict",
        "a1_class_aligned": "outputs/a1_class_aligned",
        "theory": "outputs/theory",
        "strict_freeze_rank": "outputs/strict_freeze_rank",
    }
    total = 0
    for label, rel in fams.items():
        d = PUB / rel
        if not d.exists():
            print(f"  {label:<28} missing")
            continue
        files = [f for f in d.rglob("*") if f.is_file()]
        results = [f for f in files if f.name.startswith("results") or f.name.startswith("eval_")]
        gap = [f for f in files if "gap" in f.name]
        print(f"  {label:<28} {len(files):>5} files | results/eval {len(results):>5} | "
              f"gap-history {len(gap):>5}")
        total += len(results)
    print(f"  total results/eval files across families: {total}")

    print()
    print("=" * 104)
    print("3. coco_ode_table.json content")
    print("=" * 104)
    q = PUB / "outputs/analysis/coco_ode_table.json"
    if q.exists():
        print("  " + q.read_text(encoding="utf-8", errors="ignore")[:900])

    print()
    print("=" * 104)
    print("4. ode_ledger.json: subset counts, in case 222 / 203 live there")
    print("=" * 104)
    q = PUB / "outputs/analysis/ode_ledger.json"
    if q.exists():
        d = json.loads(q.read_text(encoding="utf-8", errors="ignore"))
        print(f"  n_runs_total = {d.get('n_runs_total')}")
        for name, sub in (d.get("subsets") or {}).items():
            print(f"  subsets.{name} = {sub}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
