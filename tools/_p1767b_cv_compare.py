# -*- coding: utf-8 -*-
r"""A2 (clean rewrite): out-of-sample comparison of the four descriptions on the 862 archived trajectories.

Reports per model: median 5-fold CV R^2 (median is robust to the handful of near-constant series where R^2 is
unstable), median held-out MAE, out-of-sample win count (lowest held-out MAE per trajectory), AIC, and a paired test of
ODE against the power law on the same trajectories. Clipped predictions prevent divergent extrapolation.
"""
import glob
import io
import json
import math
import os

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rng = np.random.default_rng(0)
MODELS = ["constant", "linear", "power", "ode"]


def collect():
    out = []
    for p in glob.glob("**/gap_history.json", recursive=True):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        ep, cg = d.get("epoch"), d.get("centroid_gap")
        if isinstance(ep, list) and isinstance(cg, list) and len(ep) == len(cg) >= 5:
            t, y = np.asarray(ep, float), np.asarray(cg, float)
            if np.all(np.isfinite(t)) and np.all(np.isfinite(y)):
                out.append((t, y))
    return out


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
            p, _ = curve_fit(lambda tt, c, a, k: c + a * (1.0 - np.exp(-k * tt)),
                             t_fit, y_fit, p0=[y_fit[-1], y_fit[0] - y_fit[-1], .5],
                             bounds=([-np.inf, -np.inf, 1e-3], [np.inf, np.inf, 10.0]), maxfev=8000)
            pred = p[0] + p[1] * (1.0 - np.exp(-p[2] * t_new))
    except Exception:
        return None
    return np.clip(pred, y_fit.min() - 0.2 * span, y_fit.max() + 0.2 * span)


def cv_metrics(t, y, model, k=5, seed=0):
    n = len(t)
    idx = np.arange(n); rng2 = np.random.default_rng(seed); rng2.shuffle(idx)
    pred = np.full(n, np.nan)
    for f in np.array_split(idx, k):
        m = np.ones(n, bool); m[f] = False
        if m.sum() < 3:
            continue
        p = fit_predict(t[m], y[m], t[f], model)
        if p is not None:
            pred[f] = p
    ok = np.isfinite(pred)
    if ok.sum() < 3:
        return None
    ss = float(((y[ok] - pred[ok]) ** 2).sum()); tot = float(((y[ok] - y[ok].mean()) ** 2).sum())
    r2 = 1.0 - ss / tot if tot > 0 else float("nan")
    mae = float(np.abs(y[ok] - pred[ok]).mean())
    return r2, mae


def in_sample_aic(t, y, model):
    span = float(y.max() - y.min()) or 1.0
    try:
        if model == "constant":
            yh = np.full_like(y, y.mean()); kpar = 1
        elif model == "linear":
            yh = np.polyval(np.polyfit(t, y, 1), t); kpar = 2
        elif model == "power":
            p, _ = curve_fit(lambda tt, c, a, q: c + a * np.power(np.maximum(tt, 1e-9), q), t, y,
                             p0=[y[-1], y[0] - y[-1], .5], maxfev=8000)
            yh = p[0] + p[1] * np.power(np.maximum(t, 1e-9), p[2]); kpar = 3
        else:
            p, _ = curve_fit(lambda tt, c, a, k: c + a * (1.0 - np.exp(-k * tt)), t, y,
                             p0=[y[-1], y[0] - y[-1], .5],
                             bounds=([-np.inf, -np.inf, 1e-3], [np.inf, np.inf, 10.0]), maxfev=8000)
            yh = p[0] + p[1] * (1.0 - np.exp(-p[2] * t)); kpar = 3
    except Exception:
        return float("inf")
    ss = float(((y - yh) ** 2).sum()); n = len(y)
    return n * math.log(ss / n + 1e-12) + 2 * kpar


data = collect()
print("trajectories:", len(data))
res = {m: {"cv_r2": [], "cv_mae": [], "aic": []} for m in MODELS}
wins = {m: 0 for m in MODELS}
for t, y in data:
    per_model_mae = {}
    for m in MODELS:
        r = cv_metrics(t, y, m)
        if r is None:
            continue
        res[m]["cv_r2"].append(r[0]); res[m]["cv_mae"].append(r[1]); per_model_mae[m] = r[1]
        res[m]["aic"].append(in_sample_aic(t, y, m))
    if per_model_mae:
        wins[min(per_model_mae, key=per_model_mae.get)] += 1

summary = {}
for m in MODELS:
    r2 = np.array([x for x in res[m]["cv_r2"] if np.isfinite(x)], float)
    mae = np.array([x for x in res[m]["cv_mae"] if np.isfinite(x)], float)
    aic = np.array([x for x in res[m]["aic"] if np.isfinite(x)], float)
    summary[m] = {"median_cv_r2": float(np.median(r2)) if len(r2) else float("nan"),
                  "median_cv_mae": float(np.median(mae)) if len(mae) else float("nan"),
                  "mean_aic": float(aic.mean()) if len(aic) else float("nan"),
                  "wins_cv_mae": wins[m], "n": int(len(r2))}
    print("  %-9s medianCV_R2=%.4f medianCV_MAE=%.4f wins=%d AIC=%.1f"
          % (m, summary[m]["median_cv_r2"], summary[m]["median_cv_mae"], wins[m], summary[m]["mean_aic"]))

paired = [(a, b) for a, b, c in zip(res["ode"]["cv_mae"], res["power"]["cv_mae"], [1] * len(res["ode"]["cv_mae"]))
          if np.isfinite(a) and np.isfinite(b)]
if paired:
    d = np.array([p[1] - p[0] for p in paired])  # power MAE - ODE MAE: positive favours ODE
    tt = stats.ttest_1samp(d, 0.0)
    summary["power_minus_ode_mae"] = {"mean": float(d.mean()), "t": float(tt.statistic), "p": float(tt.pvalue),
                                      "n": int(len(d))}
    print("power MAE - ODE MAE: %+.5f (t=%.2f, p=%.2e, n=%d)" % (d.mean(), tt.statistic, tt.pvalue, len(d)))

io.open("outputs/analysis/paperA_competing_models_cv.json", "w", encoding="utf-8", newline="").write(
    json.dumps({"script": "tools/_p1767b_cv_compare.py", "n_trajectories": len(data), "models": summary}, indent=2))
print("wrote outputs/analysis/paperA_competing_models_cv.json")
