# -*- coding: utf-8 -*-
r"""Analysis of the real fine-tuning campaign: matched-gap pairs and margin mass as a per-epoch monitor.

Reads
  outputs/analysis/a1_campaign.json          per-checkpoint top-1, CG, tau_5, M(0.01), M(0.02)
  outputs/analysis/a1_campaign_correct.npz   per-checkpoint per-image correctness on the holdout

Produces outputs/analysis/a1_campaign_analysis.json with
  * checkpoint/run counts and the spread of CG and top-1 reached by the campaign;
  * matched-gap pairs at |dCG| <= 0.03 (all pairs and within-run pairs), the widest spread and its paired-bootstrap CI;
  * Pearson correlations of CG, tau_5 and M(eps) with top-1 across checkpoints;
  * per-run epoch selection: oracle, min-CG, max-tau, min-M, and last-epoch rules, with regrets.

    python tools/_p1320_campaign_analysis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
from itertools import combinations

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANA = os.path.join(REPO, "outputs", "analysis")
CAMPAIGN = os.path.join(ANA, "a1_campaign.json")
CORRECT = os.path.join(ANA, "a1_campaign_correct.npz")
OUT = os.path.join(ANA, "a1_campaign_analysis.json")


def boot_ci(correct_a, correct_b, n_boot=1000, seed=0):
    rng = np.random.RandomState(seed)
    n = len(correct_a)
    diffs = []
    for _ in range(n_boot):
        idx = rng.randint(0, n, n)
        diffs.append(float(correct_a[idx].mean() - correct_b[idx].mean()) * 100.0)
    return [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    camp = json.load(io.open(CAMPAIGN, encoding="utf-8"))
    corr = np.load(CORRECT)
    runs = camp["runs"]
    ck = []
    for key, run in runs.items():
        for c in run["checkpoints"]:
            row = dict(c)
            row.update({"run": key, "dataset": run["dataset"], "tower": run["tower"], "seed": run["seed"],
                        "ckey": f"{key}|ep{c['epoch']}"})
            ck.append(row)
    print(f"  checkpoints: {len(ck)} from {len(runs)} runs")
    out = {"n_runs": len(runs), "n_checkpoints": len(ck),
           "datasets": sorted({r["dataset"] for r in runs.values()}),
           "towers": sorted({r["tower"] for r in runs.values()}),
           "seeds": sorted({r["seed"] for r in runs.values()}),
           "cg_range": [min(r["CG"] for r in ck), max(r["CG"] for r in ck)],
           "top1_range": [min(r["top1"] for r in ck), max(r["top1"] for r in ck)],
           "protocol": camp["protocol"]}
    print(f"  CG range {out['cg_range'][0]:.4f}..{out['cg_range'][1]:.4f} | "
          f"top-1 range {out['top1_range'][0]:.2f}..{out['top1_range'][1]:.2f}")

    # ---- matched-gap pairs
    def pairs(tol, same_run=False):
        res = []
        for x, y in combinations(ck, 2):
            if same_run and x["run"] != y["run"]:
                continue
            dcg = abs(x["CG"] - y["CG"])
            if dcg <= tol:
                res.append({"a": x, "b": y, "dCG": dcg, "dtop1": abs(x["top1"] - y["top1"])})
        return res

    all_p = pairs(0.03)
    within = pairs(0.03, same_run=True)
    print(f"  pairs at |dCG|<=0.03: {len(all_p)} (within run: {len(within)})")
    widest = {}
    for name, pool in (("all", all_p), ("within_run", within)):
        if not pool:
            widest[name] = None
            continue
        best = max(pool, key=lambda p: p["dtop1"])
        ca = corr[best["a"]["ckey"]].astype(float)
        cb = corr[best["b"]["ckey"]].astype(float)
        ci = boot_ci(ca, cb)
        widest[name] = {"dCG": best["dCG"], "dtop1": best["dtop1"],
                        "a": {k: best["a"][k] for k in ("dataset", "tower", "seed", "epoch", "CG", "top1")},
                        "b": {k: best["b"][k] for k in ("dataset", "tower", "seed", "epoch", "CG", "top1")},
                        "ci95_of_dtop1": ci}
        print(f"  widest {name}: {best['dtop1']:.2f} points at dCG={best['dCG']:.4f} CI {ci}")
    out["pairs"] = {"n_all": len(all_p), "n_within_run": len(within), "widest": widest,
                    "n_pairs_at_tol": {str(t): len(pairs(t)) for t in (0.01, 0.02, 0.03, 0.05)}}

    # ---- correlations across checkpoints
    from scipy import stats as st
    top1 = np.array([r["top1"] for r in ck])
    out["correlation"] = {}
    for name, getter in (("CG", lambda r: r["CG"]), ("tau5", lambda r: r["tau5"]),
                         ("M(0.01)", lambda r: r["mass_0.01"]), ("M(0.02)", lambda r: r["mass_0.02"])):
        v = np.array([getter(r) for r in ck], dtype=float)
        ok = np.isfinite(v)
        out["correlation"][name] = float(st.pearsonr(v[ok], top1[ok])[0]) if ok.sum() > 2 else None
    print("  correlations with top-1:", {k: (round(v, 3) if v is not None else None)
                                         for k, v in out["correlation"].items()})

    # ---- per-run epoch selection
    rules = {"oracle": lambda rs: int(np.argmax([r["top1"] for r in rs])),
             "min_CG": lambda rs: int(np.argmin([r["CG"] for r in rs])),
             "max_tau5": lambda rs: int(np.argmax([r["tau5"] if r["tau5"] is not None else -9 for r in rs])),
             "min_M(0.01)": lambda rs: int(np.argmin([r["mass_0.01"] for r in rs])),
             "last_epoch": lambda rs: len(rs) - 1}
    regrets = {k: [] for k in rules}
    selections = []
    for key, run in runs.items():
        rs = run["checkpoints"]
        tops = [r["top1"] for r in rs]
        oracle = max(tops)
        row = {"run": key, "oracle_top1": oracle}
        for name, fn in rules.items():
            i = fn(rs)
            reg = oracle - tops[i]
            regrets[name].append(reg)
            row[name] = {"epoch": rs[i]["epoch"], "top1": tops[i], "regret": reg}
        selections.append(row)
    out["selection"] = {"per_run": selections,
                        "summary": {k: {"mean_regret": float(np.mean(v)), "max_regret": float(np.max(v))}
                                    for k, v in regrets.items()}}
    print("  selection regret (mean):", {k: round(v["mean_regret"], 2)
                                        for k, v in out["selection"]["summary"].items()})
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
