# -*- coding: utf-8 -*-
r"""A1: compare stopping rules from the certificate against common confidence signals.

Reads outputs/analysis/a1_stopping_baselines.json (produced by tools/_p1369_a1_stopping_baselines.py) and reports, per
signal: the selected epoch, the resulting accuracy and the regret against the labelled oracle. Writes
outputs/analysis/a1_stopping_baselines_rules.json.

    python tools/_p1375_a1_baseline_rules.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(REPO, "outputs", "analysis", "a1_stopping_baselines.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a1_stopping_baselines_rules.json")
SELECT = {
    "min_M": ("mass_0.01", min),
    "min_CG": ("CG", min),
    "min_entropy": ("entropy", min),
    "max_softmax": ("maxsoftmax", max),
    "max_logit": ("maxlogit", max),
    "min_energy": ("energy", min),
    "first": (None, None),
    "last": (None, None),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(IN, encoding="utf-8"))
    runs = d["runs"]
    per_run = {}
    for key, rows in runs.items():
        tops = [r["top1"] for r in rows]
        oracle = max(tops)
        entry = {"oracle_epoch": int(np.argmax(tops)) + 1, "oracle_top1": oracle}
        for rule, (stat, fn) in SELECT.items():
            if stat is None:
                i = 0 if rule == "first" else len(rows) - 1
            else:
                vals = [r[stat] for r in rows]
                i = int(np.argmin(vals) if fn is min else np.argmax(vals))
            entry[f"{rule}_epoch"] = i + 1
            entry[f"{rule}_top1"] = tops[i]
        per_run[key] = entry
    summary = {}
    for rule in SELECT:
        regs = [per_run[k]["oracle_top1"] - per_run[k][f"{rule}_top1"] for k in per_run]
        summary[rule] = {"mean_regret": float(np.mean(regs)), "max_regret": float(np.max(regs)), "n": len(regs)}
    breakdown = {}
    for group in ("dtd", "food101", "fathomnet8"):
        keys = [k for k in per_run if k.startswith(group)]
        if not keys:
            continue
        breakdown[group] = {rule: {"mean_regret": float(np.mean([per_run[k]["oracle_top1"] - per_run[k][f"{rule}_top1"] for k in keys]))}
                            for rule in SELECT}
    from scipy import stats as st
    mass = [r["mass_0.01"] for rows in runs.values() for r in rows]
    ent = [r["entropy"] for rows in runs.values() for r in rows]
    top = [r["top1"] for rows in runs.values() for r in rows]
    corr = {"pooled_M": float(st.pearsonr(mass, top)[0]), "pooled_entropy": float(st.pearsonr(ent, top)[0]),
            "n": len(top)}
    out = {"rules": summary, "breakdown": breakdown, "correlation": corr, "per_run": per_run}
    print("  rule           mean regret   max regret")
    for rule, v in summary.items():
        print(f"  {rule:<14} {v['mean_regret']:.2f}          {v['max_regret']:.2f}")
    print("  correlations:", {k: round(v, 3) for k, v in corr.items() if isinstance(v, float)})
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
