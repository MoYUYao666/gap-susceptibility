# -*- coding: utf-8 -*-
r"""Item 1: are the differences between statistics significant? Williams test for dependent correlations.

Both statistics are correlated with the same accuracy vector, so their correlations are dependent samples; the Williams
(1959) test is the appropriate one. Reported for classification and retrieval, for the pairs (CG, M(0.01)), (tau, M(0.01))
and (CG, tau).

    python tools/_p1314_williams.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "outputs", "analysis", "a1_statistic_showdown.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a1_williams_tests.json")


def williams(r_xy, r_zy, r_xz, n):
    """Two-sided Williams test for r_xy == r_zy with shared y (Williams 1959, as in Steiger 1980)."""
    det = 1.0 - r_xy ** 2 - r_zy ** 2 - r_xz ** 2 + 2.0 * r_xy * r_zy * r_xz
    det = max(det, 1e-12)
    denom = (2.0 * (n - 1) / (n - 3)) * det + ((r_xy + r_zy) ** 2) / 4.0 * (1.0 - r_xz) ** 3
    t = (r_xy - r_zy) * np.sqrt(((n - 1) * (1.0 + r_xz)) / denom)
    df = n - 3
    p = 2.0 * (1.0 - stats.t.cdf(abs(t), df))
    return float(t), float(df), float(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(SRC, encoding="utf-8"))
    out = {}
    for scen in ("classification", "retrieval"):
        rows = d["scenarios"][scen]
        top1 = np.array([r["top1"] for r in rows])
        cg = np.array([r["CG"] for r in rows])
        tau = np.array([r["tau5"] for r in rows])
        m1 = np.array([r["mass_0.01"] for r in rows])
        n = len(top1)
        r = {"n": n,
             "r_CG": float(stats.pearsonr(cg, top1)[0]),
             "r_tau": float(stats.pearsonr(tau, top1)[0]),
             "r_M1": float(stats.pearsonr(m1, top1)[0]),
             "r_pred_CG_tau": float(stats.pearsonr(cg, tau)[0]),
             "r_pred_CG_M1": float(stats.pearsonr(cg, m1)[0]),
             "r_pred_tau_M1": float(stats.pearsonr(tau, m1)[0])}
        tests = {}
        for name, (rx, rz, rxz) in {
            "CG vs M(0.01)": (r["r_CG"], r["r_M1"], r["r_pred_CG_M1"]),
            "tau vs M(0.01)": (r["r_tau"], r["r_M1"], r["r_pred_tau_M1"]),
            "CG vs tau": (r["r_CG"], r["r_tau"], r["r_pred_CG_tau"]),
        }.items():
            t, df, p = williams(rx, rz, rxz, n)
            tests[name] = {"t": t, "df": df, "p": p, "significant_at_0.05": bool(p < 0.05)}
        r["williams"] = tests
        out[scen] = r
        print(f"  [{scen}] n={n}")
        for k, v in tests.items():
            print(f"    {k:<16} t={v['t']:+.2f} df={v['df']} p={v['p']:.2e} sig={v['significant_at_0.05']}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
