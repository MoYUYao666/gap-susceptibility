# -*- coding: utf-8 -*-
r"""Robust statistics for the ten-seed rank sweep (C3 extension, local analysis)."""
from __future__ import annotations

import glob
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_robust_stats_10seed.json")


def stat(vals):
    v = np.array(vals, dtype=float)
    med = float(np.median(v))
    rng = np.random.default_rng(42)
    boots = [float(np.mean(rng.choice(v, len(v), replace=True))) for _ in range(2000)]
    return {"n": len(v), "mean": float(v.mean()), "sd": float(v.std(ddof=1)),
            "median": med, "mad": float(np.median(np.abs(v - med))),
            "min": float(v.min()), "max": float(v.max()),
            "ci95_mean": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}


def main() -> int:
    runs = {}
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r*_s*.json")):
        if "imgs" in f:
            continue
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("delta_E") is None or not np.isfinite(d["delta_E"]):
            continue
        runs.setdefault(d["rank"], []).append(d["delta_E"])
    out = {"meta": {"script": "tools/_p1543_robust_stats_10seed.py", "task": "C3 ten-seed robust statistics"},
           "ranks": {str(r): stat(v) for r, v in sorted(runs.items())}}
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    for r, v in sorted(out["ranks"].items()):
        print(f"  r={r}: n={v['n']} mean={v['mean']:+.1f} sd={v['sd']:.1f} median={v['median']:+.1f} "
              f"MAD={v['mad']:.1f} CI[{v['ci95_mean'][0]:+.1f},{v['ci95_mean'][1]:+.1f}]")
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
