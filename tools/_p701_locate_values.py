# -*- coding: utf-8 -*-
r"""Locate the remaining Paper A values by exact path, over a narrow candidate set.

Phase two of building the ledger: the first exploration found the ODE and learning-rate values.
This searches a focused list of archive files for the rest - the retrieval correlations, the
n = 204 / 383 / 221 counts, the baseline R2 values, the alpha sign statistics - and prints the
exact JSON path of each, so the ledger can assert on paths instead of doing string matching.

    python tools/_p701_locate_values.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "paperhe_value_paths.json"

# file -> values we hope to find in it
HUNT = {
    "outputs/analysis/dg_r1_reproducible.json": ["-0.71", "-0.59", "204", "96", "383"],
    "outputs/analysis/ode_ledger.json": ["0.949", "0.814", "0.977", "0.922", "0.943",
                                         "0.946", "96", "222", "203"],
    "outputs/analysis/coco_ode_table.json": ["0.003", "0.006", "0.108", "0.111"],
    "outputs/analysis/pr_peft_lr_sweep.json": ["60.69", "60.87", "0.0054", "0.0016"],
    "outputs/analysis/driving_trajectory.json": ["0.943", "0.922"],
    "outputs/strict_freeze_rank/summary.json": ["0.949", "0.814"],
    "outputs/analysis/freeze_parity.json": ["117", "95", "221"],
    "outputs/analysis/lit_pool.json": ["383"],
}

LEAF = re.compile(r"^[\w\[\]@.\- ]+$")


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
    result = {}
    for rel, values in HUNT.items():
        p = PUB / rel
        if not p.exists():
            print(f"  MISSING {rel}")
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            print(f"  {rel}: {str(e)[:60]}")
            continue
        leaves = list(walk(d))
        print("=" * 104)
        print(f"{rel}   ({len(leaves)} leaves)")
        print("=" * 104)
        for v in values:
            try:
                fv = float(v)
            except ValueError:
                continue
            hits = []
            for path, val in leaves:
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    tol = 0.005 if abs(fv) >= 50 else 0.0005
                    if abs(float(val) - fv) <= tol:
                        hits.append((path, val))
            print(f"  {v:<8} -> {len(hits)} hit(s)")
            for path, val in hits[:3]:
                print(f"        {path} = {val}")
            result.setdefault(rel, {})[v] = [{"path": pa, "value": va} for pa, va in hits[:5]]
        print()
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(result, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
