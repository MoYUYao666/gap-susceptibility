# -*- coding: utf-8 -*-
r"""Local upgrade (4): is the ODE's out-of-sample advantage stratified or driven by one family?

The 5-fold CV comparison so far pools 813 trajectories. A referee's obvious follow-up is "which families carry that
result?" - so this script re-computes the comparison per family and per rank (parsed from the gap_history paths), and
reports the median CV R^2 and the ODE-vs-power gap in each stratum. Strata with fewer than 20 trajectories are reported
but marked as thin, so they cannot silently carry a conclusion.

Outputs outputs/analysis/paperA_competing_models_strata.json (English keys).
"""
import glob
import io
import json
import math
import os
import re

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS = ["constant", "linear", "power", "ode"]
MIN_STRATUM = 20


def collect():
    rows = []
    for p in glob.glob("**/gap_history.json", recursive=True):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        ep, cg = d.get("epoch"), d.get("centroid_gap")
        if not (isinstance(ep, list) and isinstance(cg, list) and len(ep) == len(cg) >= 5):
            continue
        t, y = np.asarray(ep, float), np.asarray(cg, float)
        if not (np.all(np.isfinite(t)) and np.all(np.isfinite(y))):
            continue
        low = p.lower().replace("\\", "/")
        fam = "unknown"
        for key in ("dinov2", "blip2", "qwen", "llava", "clip", "siglip", "remoteclip", "bioclip", "flava", "vit"):
            if key in low:
                fam = key
                break
        m = re.search(r"rank[_-]?(\d+)|r(\d+)(?:[^0-9]|$)", low)
        rank = int(m.group(1) or m.group(2)) if m else -1
        rows.append({"path": low, "family": fam, "rank": rank, "t": t, "y": y})
    return rows


def fit_predict(t_fit, y_fit, t_new, model):
    span = float(y_fit.max() - y_fit.min()) or 1.0
    try:
        if model == "constant":
            pred = np.full_like(t_new, y_fit.mean(), dtype=float)
        elif model == "linear":
            pred = np.polyval(np.polyfit(t_fit, y_fit, 1), t_new)
        elif model == "power":
            p, _ = curve_fit(lambda tt, c, a, q: c + a * np.power(np.maximum(tt, 1e-9), q),
                             t_fit, y_fit, p0=[y_fit[-1], y_fit[0] - y_fit[-1], .5], maxfev=8000)
            pred = p[0] + p[1] * np.power(np.maximum(t_new, 1e-9), p[2])
        else:
            p, _ = curve_fit(lambda tt, c, a, k: c + a * (1.0 - np.exp(-k * tt)), t_fit, y_fit,
                             p0=[y_fit[-1], y_fit[0] - y_fit[-1], .5],
                             bounds=([-np.inf, -np.inf, 1e-3], [np.inf, np.inf, 10.0]), maxfev=8000)
            pred = p[0] + p[1] * (1.0 - np.exp(-p[2] * t_new))
    except Exception:
        return None
    return np.clip(pred, y_fit.min() - 0.2 * span, y_fit.max() + 0.2 * span)


def cv_r2(t, y, model, k=5, seed=0):
    n = len(t)
    idx = np.arange(n); rng = np.random.default_rng(seed); rng.shuffle(idx)
    pred = np.full(n, np.nan)
    for fold in np.array_split(idx, k):
        mask = np.ones(n, bool); mask[fold] = False
        if mask.sum() < 3:
            continue
        p = fit_predict(t[mask], y[mask], t[fold], model)
        if p is not None:
            pred[fold] = p
    ok = np.isfinite(pred)
    if ok.sum() < 3:
        return float("nan")
    ss = float(((y[ok] - pred[ok]) ** 2).sum()); tot = float(((y[ok] - y[ok].mean()) ** 2).sum())
    return 1.0 - ss / tot if tot > 0 else float("nan")


def strata(rows, key):
    out = {}
    for r in rows:
        out.setdefault(r[key], []).append(r)
    return out


def summarise(subset, label):
    rec = {"n": len(subset), "thin": len(subset) < MIN_STRATUM}
    per_model = {}
    for m in MODELS:
        vals = np.array([cv_r2(r["t"], r["y"], m) for r in subset], float)
        vals = vals[np.isfinite(vals)]
        per_model[m] = float(np.median(vals)) if len(vals) else float("nan")
    rec["median_cv_r2"] = per_model
    rec["ode_minus_power"] = (per_model["ode"] - per_model["power"]) if all(
        np.isfinite(per_model[m]) for m in ("ode", "power")) else float("nan")
    rec["ode_wins_by_median"] = bool(np.isfinite(rec["ode_minus_power"]) and rec["ode_minus_power"] > 0)
    return rec


rows = collect()
print("trajectories:", len(rows))
by_family = strata(rows, "family")
by_rank = strata(rows, "rank")

res = {"script": "tools/_p1784_stratified_cv.py", "n_trajectories": len(rows), "min_stratum": MIN_STRATUM,
       "by_family": {}, "by_rank": {}, "pooled": summarise(rows, "pooled")}
for fam, sub in sorted(by_family.items(), key=lambda kv: -len(kv[1])):
    res["by_family"][fam] = summarise(sub, fam)
    r = res["by_family"][fam]
    print("family %-10s n=%3d thin=%-5s ODE %.3f power %.3f gap %+.3f" %
          (fam, r["n"], r["thin"], r["median_cv_r2"]["ode"], r["median_cv_r2"]["power"], r["ode_minus_power"]))
for rank, sub in sorted(by_rank.items()):
    res["by_rank"][str(rank)] = summarise(sub, str(rank))
    r = res["by_rank"][str(rank)]
    print("rank %-5s n=%3d thin=%-5s ODE %.3f power %.3f gap %+.3f" %
          (rank, r["n"], r["thin"], r["median_cv_r2"]["ode"], r["median_cv_r2"]["power"], r["ode_minus_power"]))
p = res["pooled"]
print("pooled n=%d ODE %.3f power %.3f gap %+.3f" %
      (p["n"], p["median_cv_r2"]["ode"], p["median_cv_r2"]["power"], p["ode_minus_power"]))
io.open("outputs/analysis/paperA_competing_models_strata.json", "w", encoding="utf-8", newline="").write(
    json.dumps(res, indent=2))
print("wrote outputs/analysis/paperA_competing_models_strata.json")
