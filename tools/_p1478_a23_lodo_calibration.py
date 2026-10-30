# -*- coding: utf-8 -*-
r"""A23: leave-one-domain-out calibration of top-1 from the order-preservation coefficient tau.

Assembles per-condition (domain, model, lambda, top1, tau) rows from the three archives (domain matrix, fish-67 margins,
sonar full protocol), then fits top1 = a + b*tau on four domains and predicts the held-out domain. The point is to separate
two claims: the *relation* transfers (positive slope, high held-out correlation) but the *absolute calibration* does not
(held-out MAE and intercept shift), so a per-domain calibration is required.

Output: outputs/analysis/a23_calib_lodo.json

    python tools/_p1477b_a23_lodo_calibration.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a23_calib_lodo.json")


def load(rel):
    return json.load(io.open(os.path.join(REPO, "outputs", rel), encoding="utf-8"))


def rows():
    out = []
    dm = load("domain_matrix.json")
    for domain in ("imagenet5k", "dtd", "food101"):
        for model, cfg in dm[domain].items():
            for r in cfg.get("rows", []):
                out.append((domain, model, r["lambda"], r["top1"], r["tau_meas"]))
    om = load("ocean_margins.json")
    for model in ("bioclip", "oceanclip"):
        for lam, r in om[model]["measured"].items():
            out.append(("fish67", model, float(lam), r["top1"], r["tau"]))
    sp = load("sonar_protocol_full.json")
    for model in ("clip_frozen", "sonar_ft_full", "clip_flickrft"):
        for r in sp[model].get("rows", []):
            if "top1" not in r or not isinstance(r.get("lambda"), (int, float)):
                continue
            out.append(("sonar", model, r["lambda"], r["top1"], r["tau_meas"]))
    return out


def linfit(x, y):
    b, a = np.polyfit(x, y, 1) if len(x) > 2 else (0.0, float(np.mean(y)))
    return float(b), float(a)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    data = rows()
    domains = sorted({r[0] for r in data})
    res = {"source": ["outputs/domain_matrix.json", "outputs/ocean_margins.json",
                      "outputs/sonar_protocol_full.json"], "per_domain": {}, "lodo": {}}
    for d in domains:
        sub = [r for r in data if r[0] == d]
        tau = np.array([r[4] for r in sub])
        top = np.array([r[3] for r in sub])
        b, a0 = linfit(tau, top)
        res["per_domain"][d] = {"n": len(sub), "slope": b, "intercept": a0,
                                "pearson": float(np.corrcoef(tau, top)[0, 1]) if len(sub) > 2 else None}
    for held in domains:
        train = [r for r in data if r[0] != held]
        test = [r for r in data if r[0] == held]
        xt = np.array([r[4] for r in train])
        yt = np.array([r[3] for r in train])
        b, a0 = linfit(xt, yt)
        xh = np.array([r[4] for r in test])
        yh = np.array([r[3] for r in test])
        pred = a0 + b * xh
        res["lodo"][held] = {"n_train": len(train), "n_test": len(test), "slope": b, "intercept": a0,
                             "mae": float(np.mean(np.abs(pred - yh))),
                             "pearson": float(np.corrcoef(xh, yh)[0, 1]) if len(xh) > 2 else None}
    print("  rows:", len(data), "domains:", domains)
    for d, r in res["lodo"].items():
        print(f"  hold out {d:11s}: n={r['n_test']:3d} slope={r['slope']:+.2f} intercept={r['intercept']:+.1f} "
              f"MAE={r['mae']:.1f} r={r['pearson']}")
    mae = [r["mae"] for r in res["lodo"].values()]
    res["summary"] = {"mean_mae": float(np.mean(mae)), "max_mae": float(np.max(mae)),
                      "mean_heldout_pearson": float(np.mean([r["pearson"] for r in res["lodo"].values()]))}
    print("  summary:", res["summary"])
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(res, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
