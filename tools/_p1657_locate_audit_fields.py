#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1657_locate_audit_fields.py -- find the exact JSON field paths for the task-21 numbers.
Read-only probe: walks the candidate archives and prints every leaf whose value matches the
number under test (tolerance) together with its dotted path."""
import json
import os
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGETS = {
    "0.160 (break-even rho)": (0.160, 0.002),
    "4.227 (relative sd)": (4.227, 0.002),
    "4.96 (rc span lo)": (4.96, 0.02),
    "46.76 (rc span hi)": (46.76, 0.02),
    "4940 (A23 scored entries)": (4940, 1),
    "29 (A23 survivors)": (29, 0.5),
    "3570.10 (alloc paired diff)": (3570.10, 0.01),
    "5524.16 (alloc CI lo)": (5524.16, 0.01),
    "1850.31 (alloc CI hi)": (1850.31, 0.01),
    "49.59 (env share pct)": (49.59, 0.01),
    "32.46 (sigma env)": (32.46, 0.01),
    "32.72 (sigma seed)": (32.72, 0.01),
    "74.9 (share CI hi pct)": (74.9, 0.05),
    "59.5 (official diff)": (59.5, 0.1),
    "150.5 (official CI lo)": (150.5, 0.1),
    "196.05 (margin)": (196.05, 0.01),
    "132.0 (replicate max spread)": (132.0, 0.05),
    "76.1 (replicate mean spread)": (76.1, 0.05),
}

CANDIDATES = [
    "outputs/analysis/p3_gamma_robustness.json",
    "outputs/analysis/p3_official_vs_reimpl.json",
    "outputs/analysis/p3_official_igu_replicates.json",
    "outputs/analysis/p3_rc_family_boundary.json",
    "outputs/analysis/p3_allocation_paired_stats.json",
    "outputs/analysis/p3_env_stack_seeds.json",
    "outputs/analysis/a23_multiencoder_transfer.json",
    "outputs/analysis/p3_second_downstream.json",
]


def walk(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, path + "." + str(k) if path else str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, "%s[%d]" % (path, i))
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield path, float(x)


for rel in CANDIDATES:
    p = ROOT / rel
    if not p.exists():
        print("MISSING", rel)
        continue
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print("PARSE FAIL", rel, e)
        continue
    leaves = list(walk(d))
    print("\n=== %s (%d leaves) ===" % (rel, len(leaves)))
    for label, (val, tol) in TARGETS.items():
        hits = [(path, v) for path, v in leaves if abs(abs(v) - val) <= tol]
        if hits:
            print("  %-36s -> %s" % (label, hits[:4]))
    # also print top-level structure hints
    if isinstance(d, dict):
        print("  top keys:", list(d.keys())[:14])
