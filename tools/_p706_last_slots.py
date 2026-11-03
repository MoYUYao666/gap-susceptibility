# -*- coding: utf-8 -*-
r"""Resolve the last few Paper A ledger slots.

Remaining: the CR1 standard error and p, the OpenCLIP BitFit R2, the constant baseline, the
alpha-sign counts, and the three experiment counts. This prints the candidate fields so the
ledger can cite the right one - or record an honest gap.

    python tools/_p706_last_slots.py [--apply]
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


def show(d, prefix, keys):
    cur = d
    for k in keys:
        cur = cur.get(k)
        if cur is None:
            print(f"  {prefix}{k}: absent")
            return
    if isinstance(cur, list) and cur and isinstance(cur[0], dict):
        print(f"  {prefix}{'.'.join(keys)}: list[{len(cur)}], first keys {list(cur[0].keys())}")
        for k2, v2 in list(cur[0].items())[:10]:
            print(f"       {k2} = {v2}")
    elif isinstance(cur, dict):
        print(f"  {prefix}{'.'.join(keys)}: {list(cur.keys())}")
        for k2, v2 in list(cur.items())[:12]:
            if isinstance(v2, (int, float, str)):
                print(f"       {k2} = {v2}")
    else:
        print(f"  {prefix}{'.'.join(keys)} = {cur}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    e = json.loads((PUB / "outputs/analysis/pr_stats_hardened.json").read_text(
        encoding="utf-8", errors="ignore"))
    print("=" * 110)
    print("pr_stats_hardened.json: CR1 fields")
    print("=" * 110)
    show(e, "", ["cluster_bootstrap", "clustered_by_design_cell"])
    show(e, "", ["cluster_bootstrap", "clustered_by_family"])
    print()
    print("  every leaf whose value is near 0.29, 0.016 or -1.05:")
    def walk(o, p="$"):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from walk(v, f"{p}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from walk(v, f"{p}[{i}]")
        else:
            yield p, o
    for path, v in walk(e):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            for t in (0.29, 0.016, -1.05):
                if abs(float(v) - t) <= 0.0005:
                    print(f"     {v:<12} {path}")
    print()
    print("=" * 110)
    print("ode_ledger.json: does it hold the OpenCLIP BitFit or the constant baseline?")
    print("=" * 110)
    d = json.loads((PUB / "outputs/analysis/ode_ledger.json").read_text(
        encoding="utf-8", errors="ignore"))
    runs = d.get("runs") or []
    sites = {}
    for r in runs:
        sites.setdefault(str(r.get("site")), 0)
        sites[str(r.get("site"))] += 1
    print(f"  sites in runs: {sites}")
    print(f"  families: {sorted({str(r.get('family')) for r in runs})}")
    print(f"  runs whose R2 rounds to 0.943: "
          f"{[ (i, r.get('family'), r.get('site'), r.get('R2')) for i, r in enumerate(runs) if isinstance(r.get('R2'), (int,float)) and abs(r['R2'] - 0.943) <= 0.0005]}")
    print()
    print("  keys on a run: " + str(list(runs[0].keys()) if runs else "-"))
    print()
    print("=" * 110)
    print("candidate CATALOGUE files (for n = 221) and freeze summaries (for 117 / 95)")
    print("=" * 110)
    for pat in ("catalog", "catalogue", "freeze_parity", "experiment_catalog"):
        for p in (PUB / "outputs").rglob("*"):
            if p.is_file() and pat in p.name.lower():
                print(f"  {p.relative_to(PUB)}  ({p.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
