# -*- coding: utf-8 -*-
r"""Search the archives for counterexample pairs: similar final gap, very different R@1 (and vice versa).

This is the empirical backbone of the "the modality gap is not a sufficient statistic for zero-shot accuracy" claim.
If such pairs exist in the already-archived runs, A1 can be upgraded from an empirical observation to an
identifiability result plus a constructed counterexample, with no new training.

    python tools/_p1198_gap_accuracy_counterexamples.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(f):
    try:
        d = json.load(io.open(f, encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    a = d.get("initial_gap") or {}
    b = d.get("final_gap") or {}
    m = d.get("final_task_metrics") or {}
    cg = None
    if "centroid_gap" in a and "centroid_gap" in b:
        cg = b["centroid_gap"] - a["centroid_gap"]
    r1 = m.get("R@1")
    dg = None
    if "distribution_gap" in a and "distribution_gap" in b:
        dg = b["distribution_gap"] - a["distribution_gap"]
    if cg is None or r1 is None:
        return None
    return {"f": os.path.relpath(f, REPO), "cgd": cg, "r1": r1, "dgd": dg,
            "params": d.get("n_trainable_params"), "exp": d.get("experiment")}


def main() -> None:
    rows = []
    for f in glob.glob(os.path.join(REPO, "outputs", "**", "results.json"), recursive=True):
        r = load(f)
        if r:
            rows.append(r)
    print(f"  runs with both final CG and R@1: {len(rows)}")

    # pairs with |dCG| <= 0.01 but |dR@1| >= 0.10  -> gap-blind to accuracy
    close_gap, big_acc = [], []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if abs(a["cgd"] - b["cgd"]) <= 0.01 and abs(a["r1"] - b["r1"]) >= 0.10:
                close_gap.append((abs(a["r1"] - b["r1"]), a, b))
            if abs(a["r1"] - b["r1"]) <= 0.005 and abs(a["cgd"] - b["cgd"]) >= 0.10:
                big_acc.append((abs(a["cgd"] - b["cgd"]), a, b))

    close_gap.sort(key=lambda x: x[0], reverse=True)
    big_acc.sort(key=lambda x: x[0], reverse=True)
    print(f"\n  === same gap (|dCG|<=0.01), different accuracy (|dR@1|>=0.10): {len(close_gap)} pairs ===")
    for d, a, b in close_gap[:5]:
        print(f"   dR@1={d:.3f}  gap {a['cgd']:+.4f} vs {b['cgd']:+.4f} | R@1 {a['r1']:.3f} vs {b['r1']:.3f}")
        print(f"      A: {a['exp']} ({a['f']})")
        print(f"      B: {b['exp']} ({b['f']})")

    print(f"\n  === same accuracy (|dR@1|<=0.005), different gap (|dCG|>=0.10): {len(big_acc)} pairs ===")
    for d, a, b in big_acc[:5]:
        print(f"   dCG={d:.3f}  R@1 {a['r1']:.3f} vs {b['r1']:.3f} | gap {a['cgd']:+.4f} vs {b['cgd']:+.4f}")
        print(f"      A: {a['exp']} ({a['f']})")
        print(f"      B: {b['exp']} ({b['f']})")


if __name__ == "__main__":
    main()
