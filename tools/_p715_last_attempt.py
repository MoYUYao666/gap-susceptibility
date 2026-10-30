# -*- coding: utf-8 -*-
r"""Last attempt at the five remaining Paper A numbers.

Targets: the CR1 standard error (0.29) and the counts 117 (mechanism), 95 (strict-freezing
controls), 221 (catalogue runs), 383 (validation experiments).

Searches the audit and inventory files specifically, printing any field whose name suggests a
count or a standard error.

    python tools/_p715_last_attempt.py [--apply]
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

CANDIDATES = [
    "outputs/analysis/statistics_audit.json",
    "outputs/analysis/seed_inventory.json",
    "outputs/analysis/coco_sweep_audit.json",
    "outputs/analysis/strict_r1_audit.json",
    "outputs/analysis/eval_paths_audit.json",
    "outputs/analysis/batch_audit.json",
    "outputs/analysis/lora_injection_audit.json",
    "outputs/analysis/p3d_manifest.json",
    "outputs/analysis/dg_r1_reproducible.json",
    "outputs/analysis/pr_stats_hardened.json",
    "outputs/analysis/pr_stats_holdout.json",
]


def walk(o, p="$"):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{p}[{i}]")
    else:
        yield p, o


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for rel in CANDIDATES:
        p = PUB / rel
        if not p.exists():
            print(f"  MISSING {rel}")
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            print(f"  {rel}: {str(e)[:50]}")
            continue
        leaves = list(walk(d))
        top = list(d.keys())[:10] if isinstance(d, dict) else f"list[{len(d)}]"
        print("=" * 112)
        print(f"{rel}   ({len(leaves)} leaves)")
        print(f"  top-level: {top}")
        # counts and standard errors
        shown = 0
        for path, v in leaves:
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            key = path.split(".")[-1].split("[")[0]
            interesting = (
                (re.search(r"^n$|_n$|^n_|count|total|n_runs|n_experiments|n_fits|size",
                           key, re.I) and 40 <= float(v) <= 5000)
                or (re.search(r"se|stderr|standard_error|cr1", key, re.I)
                    and 0.05 <= float(v) <= 2.0)
            )
            if interesting and shown < 14:
                print(f"     {path} = {v}")
                shown += 1
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
