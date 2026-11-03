# -*- coding: utf-8 -*-
r"""A1: analyse the extended interior-optimum monitoring run (sequential stopping rules, no future information).

Input:  outputs/analysis/a1_monitor_interior_v2.json
Output: outputs/analysis/a1_monitor_interior_v2_rules.json

    python tools/_p1361_monitor_v2_analysis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(REPO, "outputs", "analysis", "a1_monitor_interior_v2.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a1_monitor_interior_v2_rules.json")
DELTAS = [0.005, 0.01, 0.02]
CG_DELTAS = [0.005, 0.01]


def sequential(rows, key, delta):
    """Stop at the first epoch whose statistic rises by delta above its running minimum; return the best-so-far index."""
    best_i = 0
    for t in range(1, len(rows)):
        if rows[t][key] > rows[best_i][key] + delta:
            return best_i
        if rows[t][key] < rows[best_i][key]:
            best_i = t
    return best_i


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
        entry = {"oracle_epoch": int(np.argmax(tops)) + 1, "oracle_top1": oracle,
                 "last_top1": tops[-1], "first_top1": tops[0],
                 "best_mass_index": int(np.argmin([r["mass_0.01"] for r in rows])),
                 "best_cg_index": int(np.argmin([r["CG"] for r in rows]))}
        entry["minM_top1"] = tops[entry["best_mass_index"]]
        entry["minCG_top1"] = tops[entry["best_cg_index"]]
        for delta in DELTAS:
            i = sequential(rows, "mass_0.01", delta)
            entry[f"seqM{delta}_epoch"] = i + 1
            entry[f"seqM{delta}_top1"] = tops[i]
        for delta in CG_DELTAS:
            i = sequential(rows, "CG", delta)
            entry[f"seqCG{delta}_epoch"] = i + 1
            entry[f"seqCG{delta}_top1"] = tops[i]
        per_run[key] = entry

    rules = ["minM", "minCG", "last", "first"] + [f"seqM{d}" for d in DELTAS] + [f"seqCG{d}" for d in CG_DELTAS]
    summary = {}
    for rule in rules:
        regs = []
        for key, e in per_run.items():
            chosen = e[f"{rule}_top1"] if f"{rule}_top1" in e else e.get(rule + "_top1")
            regs.append(e["oracle_top1"] - chosen)
        summary[rule] = {"mean_regret": float(np.mean(regs)), "max_regret": float(np.max(regs)), "n": len(regs)}
    # breakdown by backbone and dataset
    breakdown = {}
    for group in ("vit-base-patch32", "vit-large-patch14", "dtd", "food101"):
        keys = [k for k in per_run if group in k]
        if not keys:
            continue
        g = {}
        for rule in rules:
            chosen = [per_run[k][f"{rule}_top1"] for k in keys]
            g[rule] = {"mean_regret": float(np.mean([per_run[k]["oracle_top1"] - c for k, c in zip(keys, chosen)])),
                       "max_regret": float(np.max([per_run[k]["oracle_top1"] - c for k, c in zip(keys, chosen)]))}
        breakdown[group] = g
    # pooled and within-run correlations
    mass = [r["mass_0.01"] for rows in runs.values() for r in rows]
    top = [r["top1"] for rows in runs.values() for r in rows]
    cg = [r["CG"] for rows in runs.values() for r in rows]
    from scipy import stats as st
    corr = {"pooled_M": float(st.pearsonr(mass, top)[0]), "pooled_CG": float(st.pearsonr(cg, top)[0]),
            "within_run_M_mean": float(np.mean([st.pearsonr([r["mass_0.01"] for r in rows],
                                                          [r["top1"] for r in rows])[0] for rows in runs.values()])),
            "n_checkpoints": len(top)}
    payload = {"input": "a1_monitor_interior_v2.json", "rules": summary, "breakdown": breakdown,
               "correlation": corr, "per_run": per_run}
    print("  rules (mean regret / max regret):")
    for rule, v in summary.items():
        print(f"   {rule:<10} {v['mean_regret']:.2f} / {v['max_regret']:.2f}")
    print(f"  pooled n={corr['n_checkpoints']} r(M)={corr['pooled_M']:+.3f} r(CG)={corr['pooled_CG']:+.3f} "
          f"within-run r(M)={corr['within_run_M_mean']:+.3f}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
