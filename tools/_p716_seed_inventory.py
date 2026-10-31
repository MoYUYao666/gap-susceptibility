# -*- coding: utf-8 -*-
r"""Test whether Paper A's n = 383 and n = 221 come from the seed inventory.

outputs/analysis/seed_inventory.json has total_results = 417 and groups by configuration. The
paper says 383 experiments in the validation part and 221 runs in the experiment catalogue, so
one of the group totals may be the number. This prints the group structure and the candidate sums.

    python tools/_p716_seed_inventory.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads((PUB / "outputs/analysis/seed_inventory.json").read_text(
        encoding="utf-8", errors="ignore"))
    print(f"  total_results = {d.get('total_results')}")
    print(f"  need_upgrade  = {len(d.get('need_upgrade') or [])}")
    print(f"  already_ok    = {len(d.get('already_ok') or [])}")
    groups = d.get("groups") or []
    print(f"  groups        = {len(groups)}")
    if groups:
        print(f"  group keys    = {list(groups[0].keys())}")
        print()
        print("  first 10 groups:")
        for g in groups[:10]:
            print("    " + json.dumps(g, ensure_ascii=False)[:200])

    # sums over plausible subsets
    print()
    print("  candidate sums:")
    def sm(pred, label):
        n = sum(1 for g in groups if pred(g))
        seeds = sum(int(g.get("n_seeds") or 0) for g in groups if pred(g))
        print(f"    {label:<46} groups={n:>4}  sum(n_seeds)={seeds:>5}")

    sm(lambda g: True, "all groups")
    for key in ("dataset", "model", "family", "backbone", "config", "tag"):
        vals = {}
        for g in groups:
            v = str(g.get(key, ""))
            if v:
                vals[v] = vals.get(v, 0) + 1
        if vals:
            print(f"    by {key}: {dict(sorted(vals.items(), key=lambda kv: -kv[1])[:8])}")

    # look for any group field whose total is 383 or 221
    print()
    counter = {}
    for g in groups:
        for k, v in g.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                counter.setdefault(k, []).append(v)
    for k, vals in counter.items():
        if len(vals) > 3:
            print(f"    field {k!r}: sum={sum(vals)}, n={len(vals)}, "
                  f"min={min(vals)}, max={max(vals)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
