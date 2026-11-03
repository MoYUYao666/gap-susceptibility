# -*- coding: utf-8 -*-
r"""Test whether A1's closed-form (aggregate-level) predictor actually predicts the measured curves.

The manuscript admits its r = 1.000 is "self-consistency, not independent validation". The reason is that the *exact*
predictor inverts the very per-image margins that define the measured tau, so agreement is nearly tautological.

The *Gaussian* branch is different: it replaces the per-image margin field by the aggregate law
    tau_pred(lambda) = 1 - 2 * E[ Phi_bar( d / (|lambda| * ||g|| * sigma_b) ) ],   sigma_b = sqrt(2) * std(m)
i.e. it uses only a margin distribution and a bias scale. If that closed form tracks the independent measurement, A1
gains the missing independent validation without a single new forward pass.

This script quantifies it from outputs/a1_margins.json (ImageNet-5k, CLIP ViT-B/32), where both the predicted and the
measured curves are archived.

    python tools/_p1205_validate_a1_closed_form.py [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_closed_form_validation.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(SRC, encoding="utf-8"))
    meta = d["meta"]
    lam = sorted(float(k) for k in d["predicted_tau_exact"])
    print("  meta:", {k: meta[k] for k in ("n_images", "gap_norm", "std_m", "sigma_b", "mean_m")})

    meas5 = d["measured_tau_5k"]
    meas50 = d["measured_tau_50k"]
    print(f"  lambda grid: {lam}")
    print(f"  measured keys (5k): {sorted(meas5, key=float)}")
    print(f"  measured keys (50k): {sorted(meas50, key=float)}")

    def keys_for(l):
        """the archive stores integral lambdas without a trailing .0 in the 5k record"""
        out = []
        for k in (str(l), str(int(l)) if float(l).is_integer() else str(l), "%.2f" % l):
            if k not in out:
                out.append(k)
        return out

    indep = d.get("margin_bias_independence", {})
    print("\n  margin/bias independence (assumption of the closed form):",
          {k: round(v, 4) if isinstance(v, float) else v for k, v in indep.items()})

    rows = []
    print("\n  lam    tau_meas5   tau_gauss   tau_exact   |d_gauss|   |d_exact|   top1_meas  top1_gauss")
    for l in lam:
        k = next((x for x in keys_for(l) if x in meas5), None)
        if k is None:
            continue
        m5 = meas5[k]["tau"]
        g = d["predicted_tau_gauss"][k]
        e = d["predicted_tau_exact"][k]
        r1loss = d["predicted_rank1_loss_gauss"][k]
        top1 = meas5[k]["top1"]
        # the 5k sweep has no lambda=0 point; the frozen top-1 lives in the 50k record
        top1_frozen = None
        for key in ("0.0", "0"):
            if key in meas50 and meas50[key].get("top1") is not None:
                top1_frozen = meas50[key]["top1"]
                break
        if top1_frozen is None:
            top1_frozen = max(v["top1"] for v in meas50.values())
        top1_pred = top1_frozen * (1.0 - r1loss)
        rows.append(dict(lam=l, tau_meas=m5, tau_gauss=g, tau_exact=e,
                         top1_meas=top1, top1_gauss=top1_pred))
        print(f"  {l:>5.2f}  {m5:>9.4f}  {g:>9.4f}  {e:>9.4f}  {abs(g - m5):>9.4f}  {abs(e - m5):>9.4f}"
              f"  {top1:>8.2f}  {top1_pred:>9.2f}")

    tm = np.array([r["tau_meas"] for r in rows])
    tg = np.array([r["tau_gauss"] for r in rows])
    te = np.array([r["tau_exact"] for r in rows])
    t1m = np.array([r["top1_meas"] for r in rows])
    t1g = np.array([r["top1_gauss"] for r in rows])

    def block(name, m, p):
        mae = float(np.mean(np.abs(m - p)))
        r = float(stats.pearsonr(m, p)[0]) if len(m) > 2 and np.std(p) > 1e-12 else float("nan")
        print(f"  {name:<28} MAE={mae:.4f}  pearson r={r:.4f}  max|err|={float(np.max(np.abs(m-p))):.4f}")
        return {"mae": mae, "pearson_r": r, "max_abs_err": float(np.max(np.abs(m - p)))}

    print("\n  === agreement with measured tau (5k, same sample) ===")
    res = {"tau_gauss": block("closed form (Gauss)", tm, tg),
           "tau_exact": block("per-image inversion (exact)", tm, te)}
    print("\n  === agreement with measured top-1 ===")
    res["top1_gauss"] = block("closed form -> top-1", t1m, t1g)

    # 50k is a different, larger sample: the closest thing to an independent measurement in the archive
    rows50 = []
    for l in lam:
        k50 = next((x for x in (str(l), "%.1f" % l) if x in meas50), None)
        kg = str(l)
        if k50 is None or kg not in d["predicted_tau_gauss"] or meas50[k50].get("tau") is None:
            continue
        rows50.append((meas50[k50]["tau"], d["predicted_tau_gauss"][kg], d["predicted_tau_exact"][kg]))
    if rows50:
        m50 = np.array([r[0] for r in rows50])
        g50 = np.array([r[1] for r in rows50])
        e50 = np.array([r[2] for r in rows50])
        print("\n  === agreement with measured tau on 50k sample (independent draw) ===")
        res["tau_gauss_50k"] = block("closed form (Gauss), 50k", m50, g50)
        res["tau_exact_50k"] = block("per-image inversion, 50k", m50, e50)

    payload = {"source": "outputs/a1_margins.json", "model": "CLIP ViT-B/32 frozen (ImageNet-5k)",
               "lambda_grid": lam, "rows": rows, "summary": res,
               "note": ("The exact branch inverts the same per-image margins that define the measured tau, so its "
                        "agreement is near-tautological; the Gaussian branch uses only aggregate scales and is the "
                        "candidate independent predictor.")}
    if a.apply:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("\n  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
