# -*- coding: utf-8 -*-
r"""Robust statistics for the paper's comparisons (C3): median absolute deviation, worst case, bootstrap CI.

    python tools/_p1538_robust_stats.py
"""
from __future__ import annotations

import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
OUT = os.path.join(AN, "p3_robust_stats.json")


def stat(vals):
    v = np.array(vals, dtype=float)
    n = len(v)
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med)))
    rng = np.random.default_rng(42)
    boots = [float(np.mean(rng.choice(v, n, replace=True))) for _ in range(2000)]
    return {"n": n, "mean": float(v.mean()), "sd": float(v.std(ddof=1)) if n > 1 else None,
            "median": med, "mad": mad, "min": float(v.min()), "max": float(v.max()),
            "ci95_mean": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}


def main() -> int:
    seeds = json.load(io.open(os.path.join(AN, "p3_seeds_combined.json"), encoding="utf-8"))
    out = {"meta": {"script": "tools/_p1538_robust_stats.py", "task": "C3 robust statistics"},
           "seed5": {}}
    for rank, vals in seeds["values"].items():
        out["seed5"][rank] = stat(list(vals.values()))
    # allocation arms
    import glob
    arms = {}
    for f in glob.glob(os.path.join(REPO, "paper3", "scripts", "outputs", "experiments",
                                    "verify_r1_s42_bcexplicit*.json")):
        d = json.load(io.open(f, encoding="utf-8"))
        arms[os.path.basename(f)] = {"delta_E": d.get("delta_E"), "E": d.get("E")}
    vals = [v["delta_E"] for v in arms.values() if v["delta_E"] is not None]
    out["allocation_arms"] = {"arms": arms, "across_arms": stat(vals)}
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    for k, v in out["seed5"].items():
        print(f"  seed5 {k}: mean {v['mean']:+.1f} sd {v['sd']:.1f} median {v['median']:+.1f} MAD {v['mad']:.1f} "
              f"CI[{v['ci95_mean'][0]:+.1f},{v['ci95_mean'][1]:+.1f}]")
    print("  arms across:", {k: round(v, 1) if isinstance(v, float) else v for k, v in out["allocation_arms"]["across_arms"].items() if k != "ci95_mean"})
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
