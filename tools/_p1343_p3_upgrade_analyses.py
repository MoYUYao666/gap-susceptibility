# -*- coding: utf-8 -*-
r"""P3 upgrade analyses (all from archives, no new runs).

  P3-P0-1  theory vs random allocation: paired end-energy difference and bootstrap CI
  P3-P0-2  within-family critical rank: per-rank final energy of the sweep protocol, divergence onset
  P3-P0-3  AdaLoRA comparison: per-sample alignment-energy change against the theory/random arms

Outputs: outputs/analysis/p3_upgrade_analysis.json

    python tools/_p1343_p3_upgrade_analyses.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_upgrade_analysis.json")


def last_finite(seq):
    vals = [v for v in seq if v is not None and np.isfinite(v)]
    return vals[-1] if vals else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}

    # ---------------------------------------------------------------- theory vs random
    allr = json.load(io.open(os.path.join(EXP, "all_results.json"), encoding="utf-8"))
    theory = [r for r in allr["Theory"] if r.get("ok")]
    random = [r for r in allr["Random"] if r.get("ok")]
    pairs = []
    for t in theory:
        cands = [r for r in random if r["seed"] == t["seed"] and r["rank"] == t["rank"]]
        if not cands:
            continue
        r = min(cands, key=lambda x: abs(last_finite(x["E"]) - last_finite(t["E"])))
        et, er = last_finite(t["E"]), last_finite(r["E"])
        if et is None or er is None:
            continue
        pairs.append({"seed": t["seed"], "rank": t["rank"], "theory_name": t["name"], "random_name": r["name"],
                      "E_theory": et, "E_random": er, "diff": et - er,
                      "dE_theory": t["E"][0] - et, "dE_random": r["E"][0] - er})
    diffs = np.array([p["diff"] for p in pairs]) if pairs else np.array([])
    rng = np.random.RandomState(0)
    boot = [float(np.mean(rng.choice(diffs, len(diffs), replace=True))) for _ in range(2000)] if len(diffs) else []
    res["theory_vs_random"] = {
        "n_pairs": len(pairs), "pairs": pairs,
        "mean_diff_end_E": float(diffs.mean()) if len(diffs) else None,
        "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))] if boot else None,
        "interpretation": "positive diff means the theory allocation ends at higher alignment energy than random",
    }
    print(f"  theory vs random: n={len(pairs)} mean diff={res['theory_vs_random']['mean_diff_end_E']}")

    # ---------------------------------------------------------------- within-family critical rank
    e2 = json.load(io.open(os.path.join(EXP, "E2_results.json"), encoding="utf-8"))
    per_rank = {}
    for r in e2["sweep"]:
        per_rank.setdefault(int(r["rank"]), []).append(r)
    rows = []
    for rank in sorted(per_rank):
        e0s, ends, diverge = [], [], 0
        for r in per_rank[rank]:
            E = [v for v in r["E"]]
            e0 = E[0]
            has_nan = any(v is None or (isinstance(v, float) and v != v) for v in E)
            f = last_finite(E)
            e0s.append(e0)
            if f is not None:
                ends.append(f)
            if has_nan or (f is not None and f > e0):
                diverge += 1
        rows.append({"rank": rank, "n": len(per_rank[rank]), "n_diverged": diverge,
                     "E0": float(np.mean(e0s)) if e0s else None,
                     "mean_final": float(np.mean(ends)) if ends else None,
                     "min_final": float(np.min(ends)) if ends else None,
                     "max_final": float(np.max(ends)) if ends else None,
                     "diverged_majority": diverge >= (len(per_rank[rank]) + 1) // 2})
    # divergence onset: first rank where no seed has a finite final energy, and the last finite rank before it
    div = [r["rank"] for r in rows if r["diverged_majority"]]
    partial = [r["rank"] for r in rows if 0 < r["n_diverged"] < r["n"]]
    conv = [r["rank"] for r in rows if not r["diverged_majority"]]
    onset = div[0] if div else None
    below = [x for x in conv if onset is not None and x < onset]
    r_c = {"first_majority_diverged_rank": onset,
           "last_converged_rank": max(below) if below else None,
           "boundary_interval": [max(below), onset] if below and onset is not None else None,
           "partial_divergence_ranks": partial}
    res["rank_sweep"] = {"rows": rows, "critical_rank": r_c}
    print("  rank sweep: converged ranks", [r["rank"] for r in rows if not r["diverged_majority"]], "| majority divergence from", r_c["first_majority_diverged_rank"])

    # ---------------------------------------------------------------- AdaLoRA comparison
    ada = json.load(io.open(os.path.join(REPO, "outputs", "analysis", "p3_alloc_runs", "adalora_summary.json"),
                            encoding="utf-8"))
    ada_runs = []
    for name, v in ada["runs"].items():
        ada_runs.append({"name": name, "seed": v.get("seed"), "lr": v.get("lr"),
                         "delta_E_per_sample_mean": v.get("delta_E_per_sample_mean"),
                         "delta_E_per_sample_sd": v.get("delta_E_per_sample_sd"),
                         "E_trajectory": v.get("E_trajectory")})
    ours = []
    for grp in ("Theory", "Random"):
        for r in allr[grp]:
            if not r.get("ok") or not r["E"]:
                continue
            fin = last_finite(r["E"])
            ours.append({"group": grp, "name": r["name"], "rank": r["rank"], "seed": r["seed"],
                         "dE": r["E"][0] - fin if fin is not None else None,
                         "end_E": fin})
    res["adalora_comparison"] = {"adalora_runs": ada_runs, "our_runs": ours}
    print(f"  adalora runs: {len(ada_runs)} | our runs: {len(ours)}")

    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(res, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
