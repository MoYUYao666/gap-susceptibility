# -*- coding: utf-8 -*-
r"""A1: combine the monitoring archives (v2 + extra seeds/domain) into one rule comparison.

Reads outputs/analysis/a1_monitor_interior_v2.json and a1_monitor_interior_extra.json, computes the same stopping-rule
regrets and correlations, and writes outputs/analysis/a1_monitor_combined.json.

    python tools/_p1398_a1_combined.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
from scipy import stats as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_monitor_combined.json")
DELTA = 0.01


def sequential(rows, key, delta):
    best = 0
    for t in range(1, len(rows)):
        if rows[t][key] > rows[best][key] + delta:
            return best
        if rows[t][key] < rows[best][key]:
            best = t
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    runs = {}
    for name in ("a1_monitor_interior_v2.json", "a1_monitor_interior_extra.json"):
        p = os.path.join(REPO, "outputs", "analysis", name)
        if os.path.exists(p):
            runs.update(json.load(io.open(p, encoding="utf-8"))["runs"])
    per_run = {}
    for key, rows in runs.items():
        tops = [r["top1"] for r in rows]
        oracle = max(tops)
        entry = {"oracle": oracle}
        for rule, stat, fn in (("minM", "mass_0.01", "min"), ("minCG", "CG", "min"),
                               ("minEntropy", "entropy", "min"), ("maxSoftmax", "maxsoftmax", "max"),
                               ("maxLogit", "maxlogit", "max"), ("minEnergy", "energy", "min")):
            if not all(stat in r for r in rows):
                continue
            vals = [r[stat] for r in rows]
            i = int(np.argmin(vals) if fn == "min" else np.argmax(vals))
            entry[rule] = tops[i]
        entry["seqM"] = tops[sequential(rows, "mass_0.01", DELTA)]
        entry["seqCG"] = tops[sequential(rows, "CG", DELTA)]
        entry["first"] = tops[0]
        entry["last"] = tops[-1]
        per_run[key] = entry
    rules = ["minM", "seqM", "minCG", "seqCG", "minEntropy", "maxSoftmax", "maxLogit", "minEnergy", "first", "last"]
    summary = {}
    for rule in rules:
        keys = [k for k in per_run if rule in per_run[k]]
        regs = [per_run[k]["oracle"] - per_run[k][rule] for k in keys]
        summary[rule] = {"mean_regret": float(np.mean(regs)), "max_regret": float(np.max(regs)),
                         "n_runs": len(keys), "n_checkpoints": int(len(keys) * (len(next(iter(runs.values())))))}
    mass = [r["mass_0.01"] for rows in runs.values() for r in rows]
    top = [r["top1"] for rows in runs.values() for r in rows]
    ent_rows = [rows for rows in runs.values() if all("entropy" in x for x in rows)]
    ent = [r["entropy"] for rows in ent_rows for r in rows]
    ent_top = [r["top1"] for rows in ent_rows for r in rows]
    corr = {"n_checkpoints": len(top),
            "pooled_M": float(st.pearsonr(mass, top)[0]),
            "pooled_entropy": float(st.pearsonr(ent, ent_top)[0]), "n_entropy": len(ent),
            "within_run_M_mean": float(np.mean([st.pearsonr([r["mass_0.01"] for r in rows],
                                                            [r["top1"] for r in rows])[0]
                                                for rows in runs.values()]))}
    out = {"n_runs": len(runs), "runs": sort_keys(runs), "per_run": per_run, "rules": summary, "correlation": corr}
    print(f"  runs={len(runs)} checkpoints={corr['n_checkpoints']}")
    for rule in rules:
        print(f"   {rule:<12} mean {summary[rule]['mean_regret']:.2f}  max {summary[rule]['max_regret']:.2f}")
    print(f"  pooled r(M)={corr['pooled_M']:+.3f} r(entropy)={corr['pooled_entropy']:+.3f} "
          f"within-run r(M)={corr['within_run_M_mean']:+.3f}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


def sort_keys(runs):
    return {k: {"n_epochs": len(v)} for k, v in sorted(runs.items())}


if __name__ == "__main__":
    raise SystemExit(main())
