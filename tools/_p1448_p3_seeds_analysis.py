# -*- coding: utf-8 -*-
r"""P3: combine the five seeds per rank at the crossing and run the exact permutation test.

Reads the existing seed-42/123 archives (p3_rerun_protocol.json, p3_rerun_extra.json) and the new seeds produced by
tools/_p1416_p3_seeds.py, then reports per-rank mean +/- sd of Delta E, the sign counts, and an exact two-sided permutation
test on the difference of means (252 splits for 5 vs 5).

Output: outputs/analysis/p3_seeds_combined.json

    python tools/_p1448_p3_seeds_analysis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import itertools
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_seeds_combined.json")


def load(rel):
    p = os.path.join(REPO, rel)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    prot = load("outputs/analysis/p3_rerun_protocol.json") or {"runs": {}}
    extra = load("outputs/analysis/p3_rerun_extra.json") or {"runs": {}}
    new = load("outputs/analysis/p3_rerun_seeds.json") or {"runs": {}}
    vals = {5: {}, 6: {}}
    for src in (prot, extra, new):
        for key, entry in src.get("runs", {}).items():
            if not entry.get("ok") or entry.get("delta_E") is None:
                continue
            rank, seed = entry.get("rank"), entry.get("seed")
            if rank in vals and key.split("_")[0] == "r%d" % rank:
                vals[rank][seed] = float(entry["delta_E"])
    if len(vals[5]) < 5 or len(vals[6]) < 5:
        print("  not enough seeds yet:", {k: sorted(v) for k, v in vals.items()})
        return 0
    v5 = [vals[5][s] for s in sorted(vals[5])]
    v6 = [vals[6][s] for s in sorted(vals[6])]
    obs = float(np.mean(v6) - np.mean(v5))
    pool = v5 + v6
    n5 = len(v5)
    count = total = 0
    for comb in itertools.combinations(range(len(pool)), n5):
        idx = set(comb)
        a_ = [pool[i] for i in comb]
        b_ = [pool[i] for i in range(len(pool)) if i not in idx]
        diff = np.mean(b_) - np.mean(a_)
        total += 1
        if abs(diff) >= abs(obs) - 1e-12:
            count += 1
    p_two = count / total
    n_pos5 = sum(1 for x in v5 if x > 0)
    n_pos6 = sum(1 for x in v6 if x > 0)
    out = {"n_seeds": {"r5": len(v5), "r6": len(v6)},
           "values": {"r5": {str(s): vals[5][s] for s in sorted(vals[5])},
                      "r6": {str(s): vals[6][s] for s in sorted(vals[6])}},
           "r5": {"mean": float(np.mean(v5)), "sd": float(np.std(v5, ddof=1)), "n_positive": n_pos5},
           "r6": {"mean": float(np.mean(v6)), "sd": float(np.std(v6, ddof=1)), "n_positive": n_pos6},
           "difference_of_means": obs,
           "permutation": {"p_two_sided": p_two, "n_splits": total,
                           "p_min_attainable": 2.0 / total},
           "source_archives": ["outputs/analysis/p3_rerun_protocol.json",
                               "outputs/analysis/p3_rerun_extra.json",
                               "outputs/analysis/p3_rerun_seeds.json"]}
    print(f"  r5: n={len(v5)} mean={out['r5']['mean']:.1f} sd={out['r5']['sd']:.1f} positive={n_pos5}")
    print(f"  r6: n={len(v6)} mean={out['r6']['mean']:.1f} sd={out['r6']['sd']:.1f} positive={n_pos6}")
    print(f"  diff={obs:.1f} exact two-sided p={p_two:.3f} (min {2.0/total:.3f})")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
