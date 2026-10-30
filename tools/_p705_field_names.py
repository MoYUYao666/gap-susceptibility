# -*- coding: utf-8 -*-
r"""Print the exact field names needed to finish the Paper A ledger.

Ten assertions failed. Some are genuine gaps; others are my guesses at field names. This prints
the real structure of the two files so the ledger asserts on fields that exist, and so a real gap
can be told apart from a wrong guess.

    python tools/_p705_field_names.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def walk(obj, path="$", depth=0):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}", depth + 1)
    elif isinstance(obj, list):
        yield path, f"list[{len(obj)}]"
    else:
        yield path, obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 110)
    print("ode_ledger.json")
    print("=" * 110)
    d = json.loads((PUB / "outputs/analysis/ode_ledger.json").read_text(
        encoding="utf-8", errors="ignore"))
    print(f"  top-level keys: {list(d.keys())}")
    print("  subsets:")
    for name, sub in d["subsets"].items():
        print(f"     {name:<20} {sub}")
    print(f"  n_configs = {d.get('n_configs')}   n_configs_lora = {d.get('n_configs_lora')}")
    runs = d.get("runs") or []
    print(f"  runs: {len(runs)} entries; first entry keys: "
          f"{list(runs[0].keys()) if runs else '-'}")
    # alpha sign statistics
    neg = [r for r in runs if isinstance(r.get("alpha"), (int, float)) and r["alpha"] < 0]
    pos = [r for r in runs if isinstance(r.get("alpha"), (int, float)) and r["alpha"] >= 0]
    print(f"  runs with alpha < 0: {len(neg)}   with alpha >= 0: {len(pos)}")
    if runs:
        fams = {}
        for r in runs:
            fams.setdefault(str(r.get("family") or r.get("tag") or "?"), []).append(r)
        print("  runs by family:")
        for k, v in sorted(fams.items()):
            print(f"     {k:<28} {len(v)}")
    # constant baseline?
    print("  searching for a constant-baseline R2 field:")
    for path, v in walk(d):
        if "const" in path.lower() and isinstance(v, (int, float)):
            print(f"     {path} = {v}")

    print()
    print("=" * 110)
    print("pr_stats_hardened.json")
    print("=" * 110)
    e = json.loads((PUB / "outputs/analysis/pr_stats_hardened.json").read_text(
        encoding="utf-8", errors="ignore"))
    print(f"  n_rows = {e.get('n_rows')}")
    for key in ("ols_slope_all", "mixed_effects", "mundlak_within_between", "design_effect",
                "cluster_bootstrap", "verdict", "sensitivity", "label_evidence"):
        v = e.get(key)
        if isinstance(v, dict):
            print(f"  {key}: {list(v.keys())}")
            for k2, v2 in list(v.items())[:12]:
                if isinstance(v2, (int, float, str)):
                    print(f"       {k2} = {v2}")
                elif isinstance(v2, dict):
                    print(f"       {k2}: {list(v2.keys())[:8]}")
                elif isinstance(v2, list):
                    print(f"       {k2}: list[{len(v2)}]")
        else:
            print(f"  {key} = {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
