# -*- coding: utf-8 -*-
r"""A23: calibration test for the order-preservation tau across the two adapted encoders.

Raw tau thresholds do not transfer because tau's scale differs between encoders. This script tests two calibrations:
(1) rank/percentile normalisation within each encoder's amplitude grid, and (2) a linear map tau -> accuracy fitted on one
encoder and evaluated on the other. The comparison is reported as is; a failure stays a failure.

Output: outputs/analysis/a23_tau_calibration.json

    python tools/_p1393_a23_tau_calibration.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
from scipy import stats as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(REPO, "outputs", "analysis", "a23_tau_control.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a23_tau_calibration.json")


def ba(pred, truth):
    tp = np.sum(pred & truth)
    tn = np.sum(~pred & ~truth)
    fp = np.sum(pred & ~truth)
    fn = np.sum(~pred & truth)
    return float(0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1)))


def percentile(x):
    x = np.asarray(x, dtype=float)
    order = np.argsort(np.argsort(x))
    return order / max(len(x) - 1, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(IN, encoding="utf-8"))
    data = {}
    for tag, v in d["models"].items():
        rows = [r for r in v["rows"] if isinstance(r["lambda"], (int, float))]
        data[tag] = {"tau": np.array([r["tau"] for r in rows]),
                     "top": np.array([r["top1"] for r in rows])}
    out = {"raw": {}, "percentile": {}, "linear": {}}
    tags = list(data)
    for fit_tag in tags:
        for test_tag in tags:
            if test_tag == fit_tag:
                continue
            f, t = data[fit_tag], data[test_tag]
            # 1) raw tau threshold
            best_ba, best_thr = 0.0, None
            for thr in np.linspace(f["tau"].min(), f["tau"].max(), 201):
                h = f["top"] <= np.median(f["top"])
                score = ba(f["tau"] >= thr, h)
                if score > best_ba:
                    best_ba, best_thr = score, thr
            key = f"{fit_tag}->{test_tag}"
            out["raw"][key] = {"fit_BA": best_ba, "test_BA": ba(t["tau"] >= best_thr, t["top"] <= np.median(t["top"]))}
            # 2) percentile normalisation
            fp, tp = percentile(f["tau"]), percentile(t["tau"])
            best_ba, best_thr = 0.0, None
            for thr in np.linspace(0, 1, 101):
                h = f["top"] <= np.median(f["top"])
                score = ba(fp >= thr, h)
                if score > best_ba:
                    best_ba, best_thr = score, thr
            out["percentile"][key] = {"fit_BA": best_ba,
                                      "test_BA": ba(tp >= best_thr, t["top"] <= np.median(t["top"]))}
            # 3) linear map tau -> accuracy fitted on the first encoder, evaluated on the second
            A = np.vstack([np.ones_like(f["tau"]), f["tau"]]).T
            coef, *_ = np.linalg.lstsq(A, f["top"], rcond=None)
            pred = coef[0] + coef[1] * t["tau"]
            out["linear"][key] = {
                "fit_MAE": float(np.mean(np.abs(coef[0] + coef[1] * f["tau"] - f["top"]))),
                "test_MAE": float(np.mean(np.abs(pred - t["top"]))),
                "test_spearman": float(st.spearmanr(pred, t["top"])[0]),
                "test_pearson": float(st.pearsonr(pred, t["top"])[0]),
            }
    print("  raw:", {k: [round(v["fit_BA"], 2), round(v["test_BA"], 2)] for k, v in out["raw"].items()})
    print("  percentile:", {k: [round(v["fit_BA"], 2), round(v["test_BA"], 2)] for k, v in out["percentile"].items()})
    print("  linear:", {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in out["linear"].items()})
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
