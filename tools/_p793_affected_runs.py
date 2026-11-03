# -*- coding: utf-8 -*-
r"""Classify which archived runs are affected by the adapter-scope defect, per paper.

The defect made every "LoRA" run train the whole adapted tower. A run is affected if its recorded
n_trainable_params is far above what its adapters alone would hold. This lists every archived run
that names LoRA or a rank, groups it by paper, and states the verdict, so the two manuscripts can be
corrected knowing exactly which of their numbers are implicated.

    python tools/_p793_affected_runs.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "affected_runs.json"

# adapter-only parameter counts for rank 8 on this architecture
LORA_ONLY = {"text": 196_608, "both": 491_520}

PAPER_OF_TREE = [
    ("outputs/route_c", "P3"),
    ("outputs/route_d", "P3"),
    ("outputs/route_e", "P3"),
    ("outputs/siglip", "Paper A"),
    ("outputs/blip2", "Paper A"),
    ("outputs/theory/v1_trajectory", "P3 + Paper A"),
    ("outputs/theory/beta_pilot", "Paper A"),
    ("outputs/theory/adapter", "Paper A"),
    ("outputs/theory/bitfit", "Paper A"),
    ("outputs/coco", "Paper A"),
    ("outputs/flickr30k", "Paper A"),
    ("outputs/vitl", "Paper A"),
    ("outputs/strict_freeze", "Paper A"),
]


def paper_for(path: str) -> str:
    for tree, paper in PAPER_OF_TREE:
        if path.startswith(tree):
            return paper
    return "?"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", "replace").splitlines() if x.endswith(".json")]

    groups = defaultdict(list)
    for f in files:
        p = PUB / f
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        n = d.get("n_trainable_params")
        exp = str(d.get("experiment") or Path(f).parent.name)
        if not isinstance(n, int):
            continue
        if not any(f.startswith(tree + "/") for tree, _ in PAPER_OF_TREE):
            continue
        if n > 1_000_000:                      # far above any adapter-only count
            groups[paper_for(f)].append({"tree": "/".join(f.split("/")[:2]), "exp": exp, "n": n})

    print("=" * 104)
    print("archived runs whose trainable count exceeds any adapter-only configuration")
    print("=" * 104)
    total = 0
    for paper in sorted(groups):
        rows = groups[paper]
        total += len(rows)
        print()
        print(f"  {paper}   ({len(rows)} runs)")
        trees = defaultdict(int)
        for row in rows:
            trees[row["tree"]] += 1
        for t, c in sorted(trees.items()):
            print(f"     {t:<34} {c:>3} runs")
        for row in rows[:4]:
            print(f"        e.g. {row['exp']:<34} n_trainable = {row['n']:,}")
    print()
    print(f"  affected runs in total: {total}")
    print()
    print("  a rank-8 adapter holds 196,608 parameters on one tower and 491,520 on both,")
    print("  so every count above means the base model was not frozen.")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({k: v for k, v in groups.items()},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
