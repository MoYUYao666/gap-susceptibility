# -*- coding: utf-8 -*-
r"""Explore the archive files that Paper A's headline numbers should come from.

Before writing assertions, the shape of each candidate source has to be known, or the ledger
degenerates into the string matching it is meant to replace. This prints, for the likely
sources, the keys and where each target value actually sits.

    python tools/_p700_explore_sources.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "paperhe_sources_explored.json"

CANDIDATES = [
    "outputs/analysis/ode_ledger.json",
    "outputs/analysis/driving_trajectory.json",
    "outputs/analysis/lit_pool.json",
    "outputs/analysis/pr_peft_lr_sweep.json",
    "outputs/analysis/pr_fullft_lr_sweep.json",
    "outputs/a1_multiseed.json",
    "outputs/analysis/coco_ode_table.json",
    "outputs/analysis/dg_r1_reproducible.json",
]

TARGETS = ["0.949", "0.814", "0.977", "0.943", "0.922", "0.946", "0.71", "0.59",
           "60.69", "60.87", "383", "204", "222", "203", "117", "95", "96"]


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
    summary = {}
    for rel in CANDIDATES:
        p = PUB / rel
        if not p.exists():
            print(f"  MISSING {rel}")
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            print(f"  {rel}: not JSON ({str(e)[:60]})")
            continue
        keys = list(d.keys()) if isinstance(d, dict) else f"list[{len(d)}]"
        print("=" * 104)
        print(f"{rel}   ({p.stat().st_size:,} bytes)")
        print("=" * 104)
        print(f"  top-level: {keys}")
        leaves = list(walk(d))
        print(f"  {len(leaves)} scalar leaves")
        # which targets appear, and where
        for t in TARGETS:
            tf = float(t)
            hits = []
            for path, val in leaves:
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    if abs(float(val) - tf) < 0.0005 or (
                            tf >= 50 and abs(float(val) - tf) < 0.005):
                        hits.append((path, val))
            if hits:
                print(f"    {t:<8} -> {hits[:3]}")
        summary[rel] = {"top_level": keys if isinstance(keys, list) else keys,
                        "leaves": len(leaves)}
        print()
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(summary, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
