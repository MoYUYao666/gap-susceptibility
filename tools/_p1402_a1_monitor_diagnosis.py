# -*- coding: utf-8 -*-
r"""A1 diagnosis: why does the minimum-mass rule lose to the last epoch on the expanded monitoring set?

The expanded set adds runs on small held-out splits (fathomnet8, inat_wild). On small splits the margin mass is quantised
to 1/n_eval, so its minimum is attained at many epochs; np.argmin then returns the earliest one, which can be a lucky early
epoch rather than the best checkpoint. This script quantifies that effect and tests the standard fix: among the epochs
attaining the minimum, take the latest one (and a smoothed variant).

Output: outputs/analysis/a1_monitor_diagnosis.json

    python tools/_p1402_a1_monitor_diagnosis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_monitor_diagnosis.json")


def load_runs():
    runs = {}
    for name in ("a1_monitor_interior_v2.json", "a1_monitor_interior_extra.json"):
        p = os.path.join(REPO, "outputs", "analysis", name)
        if os.path.exists(p):
            runs.update(json.load(io.open(p, encoding="utf-8"))["runs"])
    return runs


def dataset_of(key):
    for d in ("dtd", "food101", "fathomnet8", "inat_wild"):
        if d in key:
            return d
    return "unknown"


def quant_step(vals):
    u = sorted(set(round(v, 6) for v in vals))
    diffs = [b - a for a, b in zip(u, u[1:]) if b - a > 1e-9]
    return min(diffs) if diffs else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    runs = load_runs()
    per_run = {}
    for key, rows in runs.items():
        tops = [r["top1"] for r in rows]
        oracle = max(tops)
        m1 = [r["mass_0.01"] for r in rows]
        m2 = [r["mass_0.02"] for r in rows]
        mn1 = min(m1)
        idx_first = int(np.argmin(m1))
        idx_last = max(i for i, x in enumerate(m1) if abs(x - mn1) < 1e-12)
        smooth = np.convolve(m1, np.ones(3) / 3, mode="same")
        idx_smooth = int(np.argmin(smooth))
        step = quant_step(m1)
        entry = {
            "dataset": dataset_of(key),
            "n_epochs": len(rows),
            "oracle_top1": oracle,
            "oracle_epoch": int(np.argmax(tops)) + 1,
            "n_ties_at_min": sum(1 for x in m1 if abs(x - mn1) < 1e-12),
            "quant_step": step,
            "epoch_first": idx_first + 1, "top1_first": tops[idx_first], "regret_first": oracle - tops[idx_first],
            "epoch_last": idx_last + 1, "top1_last": tops[idx_last], "regret_last": oracle - tops[idx_last],
            "epoch_smooth": idx_smooth + 1, "top1_smooth": tops[idx_smooth], "regret_smooth": oracle - tops[idx_smooth],
            "regret_epoch_last_epoch": oracle - tops[-1],
            "regret_first_epoch": oracle - tops[0],
            "mass_0.02_epoch": int(np.argmin(m2)) + 1,
            "regret_mass_0.02": oracle - tops[int(np.argmin(m2))],
        }
        per_run[key] = entry

    def agg(rule):
        return {"mean": float(np.mean([per_run[k][rule] for k in per_run])),
                "max": float(np.max([per_run[k][rule] for k in per_run]))}

    summary = {r: agg(r) for r in ("regret_first", "regret_last", "regret_smooth", "regret_mass_0.02",
                                   "regret_epoch_last_epoch", "regret_first_epoch")}
    # split by split size (quantisation): small splits are fathomnet8 and inat_wild
    small = [k for k in per_run if per_run[k]["dataset"] in ("fathomnet8", "inat_wild")]
    large = [k for k in per_run if k not in small]
    def agg_sub(rule, keys):
        return {"mean": float(np.mean([per_run[k][rule] for k in keys]))} if keys else None
    def agg_sub(rule, keys):
        return {"mean": float(np.mean([per_run[k][rule] for k in keys]))} if keys else None
    breakdown = {"small_eval_splits": {r: agg_sub(r, small) for r in ("regret_first", "regret_last", "regret_smooth")},
                 "large_eval_splits": {r: agg_sub(r, large) for r in ("regret_first", "regret_last", "regret_smooth")}}
    ties = [per_run[k]["n_ties_at_min"] for k in per_run]
    out = {"n_runs": len(per_run), "summary": summary, "breakdown": breakdown,
           "ties_at_min_mean": float(np.mean(ties)), "per_run": per_run}
    print(f"  runs={len(per_run)} mean ties at min={np.mean(ties):.1f}")
    for rule in ("regret_first", "regret_last", "regret_smooth", "regret_mass_0.02",
                 "regret_epoch_last_epoch", "regret_first_epoch"):
        print(f"   {rule:<24} mean {summary[rule]['mean']:.2f}  max {summary[rule]['max']:.2f}")
    print("  small splits:", {k: round(v['mean'], 2) for k, v in breakdown["small_eval_splits"].items()})
    print("  large splits:", {k: round(v['mean'], 2) for k, v in breakdown["large_eval_splits"].items()})
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
