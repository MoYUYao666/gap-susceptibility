# -*- coding: utf-8 -*-
r"""Paper A: ODE-fit residual diagnostics over the archived 96 runs.

Reads outputs/analysis/ode_ledger.json (per-run alpha, beta, R2, family, site, rank) and reports the fit-quality structure:
by family, by adaptation site, by rank, the worst runs, and the beta dispersion by site. The point is to show where the
first-order reduction is reliable and where it is not, instead of reporting one mean R2.

Output: outputs/analysis/paperA_ode_residuals.json

    python tools/_p1440_paperA_ode_residuals.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
from collections import defaultdict

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "outputs", "analysis", "ode_ledger.json")
OUT = os.path.join(REPO, "outputs", "analysis", "paperA_ode_residuals.json")


def stats(vals):
    v = np.array(vals, dtype=float)
    return {"n": int(len(v)), "mean": float(v.mean()), "sd": float(v.std(ddof=1)) if len(v) > 1 else 0.0,
            "median": float(np.median(v)), "min": float(v.min()), "max": float(v.max()),
            "frac_gt_0.9": float((v > 0.9).mean())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(SRC, encoding="utf-8"))
    runs = d["runs"]
    by_family, by_site, by_rank, betas = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    worst = []
    for r in runs:
        by_family[r.get("family", "?")].append(r["R2"])
        by_site[r.get("site", "?")].append(r["R2"])
        by_rank[str(r.get("rank", "?"))].append(r["R2"])
        betas[r.get("site", "?")].append(r.get("beta", float("nan")))
        worst.append((r["R2"], {k: r.get(k) for k in ("conf", "family", "site", "rank", "alpha", "beta")}))
    worst.sort(key=lambda x: x[0])
    out = {"source": "outputs/analysis/ode_ledger.json", "n_runs": len(runs),
           "all": stats([r["R2"] for r in runs]),
           "by_family": {k: stats(v) for k, v in sorted(by_family.items())},
           "by_site": {k: stats(v) for k, v in sorted(by_site.items())},
           "by_rank": {k: stats(v) for k, v in sorted(by_rank.items())},
           "beta_by_site": {k: {"mean": float(np.nanmean(v)), "sd": float(np.nanstd(v, ddof=1)),
                                "cv": float(np.nanstd(v, ddof=1) / np.nanmean(v)) if np.nanmean(v) else None,
                                "n": int(len(v))} for k, v in sorted(betas.items())},
           "worst_runs": [{"R2": float(r2), **conf} for r2, conf in worst[:8]],
           "best_runs": [{"R2": float(r2), **conf} for r2, conf in worst[-4:]]}
    print("  all:", out["all"])
    for k, v in out["by_family"].items():
        print(f"  family {k}: n={v['n']} mean={v['mean']:.3f} min={v['min']:.3f} frac>0.9={v['frac_gt_0.9']:.2f}")
    for k, v in out["by_site"].items():
        print(f"  site {k}: n={v['n']} mean={v['mean']:.3f} min={v['min']:.3f}")
    print("  beta CV by site:", {k: round(v["cv"], 3) for k, v in out["beta_by_site"].items() if v["cv"]})
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
