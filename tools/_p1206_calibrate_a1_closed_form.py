# -*- coding: utf-8 -*-
r"""Can one calibrated constant turn A1's closed form into a quantitative predictor?

The Gaussian branch of the first-order law predicts
    tau(lambda) = 1 - 2 * E_pair[ Phi_bar( d / (|lambda| * ||g|| * sigma_b) ) ]
and tracks the measured curve's shape (r = 0.987) but sits ~0.12 too low in level. That is a bias, not a shape error,
so a single effective scale sigma_b_eff = k * sqrt(2) * sigma_m may repair it.

If one constant fitted on ImageNet brings the residual down to the sampling noise, the law becomes a one-constant
predictor -- a candidate for the out-of-benchmark test that A1 currently lacks.

    python tools/_p1206_calibrate_a1_closed_form.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "outputs", "a1_margins.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a1_closed_form_calibration.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(SRC, encoding="utf-8"))
    meta = d["meta"]
    g = float(meta["gap_norm"])
    sigma_b = float(meta["sigma_b"])
    d_pairs = np.asarray(d["pair_samples"]["d"], dtype=float)
    lam = sorted(float(k) for k in d["predicted_tau_gauss"])
    meas = d["measured_tau_5k"]
    print(f"  pairs={len(d_pairs)}  gap_norm={g:.6f}  sigma_b={sigma_b:.6f}")
    print(f"  margin d: mean={d_pairs.mean():.5f}  sd={d_pairs.std():.5f}")

    def keys_for(l):
        return [str(l), str(int(l)) if float(l).is_integer() else str(l)]

    meas_pairs = []
    for l in lam:
        k = next((x for x in keys_for(l) if x in meas), None)
        if k is None:
            continue
        meas_pairs.append((l, float(meas[k]["tau"])))
    print(f"  measured points: {len(meas_pairs)}")

    def predict(l, kscale):
        sb = max(kscale * sigma_b, 1e-9)
        u = d_pairs / (abs(l) * g * sb + 1e-12)
        return float(1.0 - 2.0 * np.mean(stats.norm.sf(u)))

    def sse(k):
        return sum((predict(l, k) - t) ** 2 for l, t in meas_pairs)

    grid = np.linspace(0.3, 1.6, 131)
    errs = [(sse(k), k) for k in grid]
    best_sse, best_k = min(errs)
    print(f"\n  uncalibrated (k=1): MAE={np.mean([abs(predict(l,1.0)-t) for l,t in meas_pairs]):.4f}")
    print(f"  best k={best_k:.3f}  MAE={np.mean([abs(predict(l,best_k)-t) for l,t in meas_pairs]):.4f}"
          f"  max|err|={max(abs(predict(l,best_k)-t) for l,t in meas_pairs):.4f}")

    print("\n   lam   measured   k=1 pred   calibrated pred")
    rows = []
    for l, t in meas_pairs:
        p1 = predict(l, 1.0)
        pc = predict(l, best_k)
        rows.append({"lambda": l, "measured": t, "pred_k1": p1, "pred_calibrated": pc})
        print(f"  {l:>5.2f}   {t:>8.4f}   {p1:>9.4f}   {pc:>14.4f}")

    res = {
        "source": SRC, "model": "CLIP ViT-B/32 frozen, ImageNet-5k",
        "n_pairs": int(len(d_pairs)), "gap_norm": g, "sigma_b": sigma_b,
        "k_best": float(best_k),
        "mae_uncalibrated": float(np.mean([abs(predict(l, 1.0) - t) for l, t in meas_pairs])),
        "mae_calibrated": float(np.mean([abs(predict(l, best_k) - t) for l, t in meas_pairs])),
        "max_abs_err_calibrated": float(max(abs(predict(l, best_k) - t) for l, t in meas_pairs)),
        "r_calibrated": float(stats.pearsonr([predict(l, best_k) for l, _ in meas_pairs],
                                             [t for _, t in meas_pairs])[0]),
        "rows": rows,
        "note": ("one constant multiplies the bias scale; the shape was already right, so a small k should absorb the "
                 "level offset. The fitted k must then be frozen and tested on the other benchmarks."),
    }
    if a.apply:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(res, indent=1))
        print("\n  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
