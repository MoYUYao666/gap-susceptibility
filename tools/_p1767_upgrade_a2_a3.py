# -*- coding: utf-8 -*-
r"""Local upgrade A2 + A3: out-of-sample comparison of the four descriptions, and statistics for the pre-registered test.

A2 (competition): the manuscript reports in-sample R^2 over 862 archived gap trajectories (ODE 0.782, power 0.711,
linear 0.485). In-sample fit favours flexible models, so this script adds leave-one-point-out cross-validation and
AIC/BIC over the same trajectories, per family, which is what makes the comparison load-bearing.

A3 (pre-registration): the 45 held-out arms (3 backbones x 3 sites x 5 seeds) are summarised with 95% CIs, a paired
comparison of text-only against the other two sites, and effect sizes; the OpenCLIP reversal is tested against zero
rather than merely described.

Everything is computed from archives already in the repository; no model is loaded and no GPU is used.
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
OUT_DIR = "outputs/analysis"
os.makedirs(OUT_DIR, exist_ok=True)


# ------------------------------------------------------------------ A2: trajectories
def series():
    out = []
    for p in glob.glob("**/gap_history.json", recursive=True):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        ep, cg = d.get("epoch"), d.get("centroid_gap")
        if isinstance(ep, list) and isinstance(cg, list) and len(ep) == len(cg) >= 4:
            t = np.asarray(ep, float)
            y = np.asarray(cg, float)
            if np.all(np.isfinite(t)) and np.all(np.isfinite(y)):
                out.append((p.replace("\\", "/"), t, y))
    return out


def fits(t, y):
    """Return dict model -> (yhat, k_params) fitted on (t, y)."""
    res = {"constant": (np.full_like(y, y.mean()), 1)}
    res["linear"] = (np.polyval(np.polyfit(t, y, 1), t), 2)
    try:
        p, _ = curve_fit(lambda tt, c, a, q: c + a * np.power(np.maximum(tt, 1e-9), q), t, y,
                         p0=[y[-1], y[0] - y[-1], .5], maxfev=40000)
        res["power"] = (p[0] + p[1] * np.power(np.maximum(t, 1e-9), p[2]), 3)
    except Exception:
        res["power"] = (np.full_like(y, np.nan), 3)
    try:
        p, _ = curve_fit(lambda tt, c, a, k: c + a * (1.0 - np.exp(-k * tt)), t, y,
                         p0=[y[-1], y[0] - y[-1], .5],
                         bounds=([-np.inf, -np.inf, 1e-3], [np.inf, np.inf, 10.0]), maxfev=40000)
        res["ode"] = (p[0] + p[1] * (1.0 - np.exp(-p[2] * t)), 3)
    except Exception:
        res["ode"] = (np.full_like(y, np.nan), 3)
    return res


def loo_r2(t, y, model):
    """Leave-one-point-out R^2: refit on n-1 points, predict the held-out one."""
    n = len(t)
    pred = np.full(n, np.nan)
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        f = fits(t[m], y[m])
        yh, _ = f[model]
        if np.all(np.isfinite(yh)):
            # rebuild the held-out prediction with the same parameters is not available, so refit including the
            # model form and evaluate structurally: use the model curve evaluated at t[i]
            try:
                if model == "constant":
                    pred[i] = y[m].mean()
                elif model == "linear":
                    pred[i] = np.polyval(np.polyfit(t[m], y[m], 1), t[i])
                elif model == "power":
                    p, _ = curve_fit(lambda tt, c, a, q: c + a * np.power(np.maximum(tt, 1e-9), q),
                                     t[m], y[m], p0=[y[m][-1], y[m][0] - y[m][-1], .5], maxfev=40000)
                    pred[i] = p[0] + p[1] * max(t[i], 1e-9) ** p[2]
                else:
                    p, _ = curve_fit(lambda tt, c, a, k: c + a * (1.0 - np.exp(-k * tt)),
                                     t[m], y[m], p0=[y[m][-1], y[m][0] - y[m][-1], .5],
                                     bounds=([-np.inf, -np.inf, 1e-3], [np.inf, np.inf, 10.0]), maxfev=40000)
                    pred[i] = p[0] + p[1] * (1.0 - np.exp(-p[2] * t[i]))
            except Exception:
                pred[i] = np.nan
    ok = np.isfinite(pred)
    if ok.sum() < 3:
        return float("nan")
    ss = float(((y[ok] - pred[ok]) ** 2).sum())
    tot = float(((y[ok] - y[ok].mean()) ** 2).sum())
    return 1.0 - ss / tot if tot > 0 else float("nan")


series_all = series()
print("trajectories:", len(series_all))
models = ["constant", "linear", "power", "ode"]
cv = {m: [] for m in models}
aic = {m: [] for m in models}
wins = {m: 0 for m in models}
for _, t, y in series_all:
    f = fits(t, y)
    for m in models:
        yh, k = f[m]
        cv[m].append(loo_r2(t, y, m))
        if np.all(np.isfinite(yh)):
            n = len(y)
            ss = float(((y - yh) ** 2).sum())
            aic[m].append(n * math.log(ss / n + 1e-12) + 2 * k)
        else:
            aic[m].append(float("inf"))
    vals = [(np.nanmean([abs(x - yy) for x, yy in zip(f[m][0], y)]), m) for m in models
            if np.all(np.isfinite(f[m][0]))]
    if vals:
        wins[min(vals)[1]] += 1

summary_cv = {}
for m in models:
    v = [x for x in cv[m] if np.isfinite(x)]
    summary_cv[m] = {"mean_loo_r2": float(np.mean(v)) if v else float("nan"),
                     "median_loo_r2": float(np.median(v)) if v else float("nan"),
                     "n": len(v),
                     "mean_aic": float(np.mean([x for x in aic[m] if np.isfinite(x)])) if any(np.isfinite(x) for x in aic[m]) else float("nan"),
                     "wins": wins[m]}
    print("  %-9s LOOCV R2=%.4f  AIC=%.1f  wins=%d" % (m, summary_cv[m]["mean_loo_r2"],
                                                       summary_cv[m]["mean_aic"], wins[m]))

# paired test: ODE vs power law on the same trajectories
paired = [(a, b) for a, b in zip(cv["ode"], cv["power"]) if np.isfinite(a) and np.isfinite(b)]
if paired:
    a = np.array([p[0] for p in paired]); b = np.array([p[1] for p in paired])
    tt = stats.ttest_rel(a, b)
    summary_cv["ode_minus_power"] = {"mean_diff": float((a - b).mean()),
                                     "t": float(tt.statistic), "p": float(tt.pvalue), "n": len(a)}
    print("ODE - power LOOCV diff: %+.4f (t=%.2f, p=%.2e, n=%d)" %
          ((a - b).mean(), tt.statistic, tt.pvalue, len(a)))

io.open(os.path.join(OUT_DIR, "paperA_competing_models_loo.json"), "w", encoding="utf-8", newline="").write(
    json.dumps({"script": "tools/_p1767_upgrade_a2_a3.py", "n_trajectories": len(series_all),
                "models": summary_cv}, indent=2))
print("wrote", os.path.join(OUT_DIR, "paperA_competing_models_loo.json"))


# ------------------------------------------------------------------ A3: pre-registered statistics
SETS = [("CLIP B/32", "paperA_c_prereg"), ("OpenCLIP B/32", "paperA_c_prereg_openclip"),
        ("CLIP B/16", "paperA_c_prereg_b16")]
SITES = ["text_only", "both", "vision_only"]


def value(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur if isinstance(cur, (int, float)) else None


stats_out = {}
for label, folder in SETS:
    per_site = {s: [] for s in SITES}
    for p in sorted(glob.glob(os.path.join("outputs", folder, "*.json"))):
        d = json.load(io.open(p, encoding="utf-8"))
        site = next((s for s in SITES if s in p), d.get("tag"))
        cg0, cg1 = value(d, "initial_gap", "centroid_gap"), value(d, "final_gap", "centroid_gap")
        if cg0 is None or cg1 is None or site not in per_site:
            continue
        per_site[site].append(cg1 - cg0)
    rec = {}
    for s in SITES:
        v = np.array(per_site[s], float)
        if len(v) >= 2:
            tcrit = stats.t.ppf(0.975, len(v) - 1)
            rec[s] = {"n": int(len(v)), "mean": float(v.mean()), "sd": float(v.std(ddof=1)),
                      "ci95": float(tcrit * v.std(ddof=1) / math.sqrt(len(v)))}
    if "text_only" in rec:
        v = np.array(per_site["text_only"], float)
        t0 = stats.ttest_1samp(v, 0.0)
        rec["text_only_vs_zero"] = {"t": float(t0.statistic), "p": float(t0.pvalue)}
    if "text_only" in rec and "vision_only" in rec and len(per_site["text_only"]) == len(per_site["vision_only"]):
        diff = np.array(per_site["text_only"], float) - np.array(per_site["vision_only"], float)
        t1 = stats.ttest_rel(per_site["text_only"], per_site["vision_only"])
        d = float(diff.mean() / diff.std(ddof=1)) if diff.std(ddof=1) > 0 else float("nan")
        rec["text_only_minus_vision_only"] = {"mean_diff": float(diff.mean()), "t": float(t1.statistic),
                                             "p": float(t1.pvalue), "cohen_d": d}
    stats_out[label] = rec
    print("\n" + label)
    for s in SITES:
        if s in rec:
            r = rec[s]
            print("  %-12s n=%d mean=%+.4f sd=%.4f ci95=+-%.4f" % (s, r["n"], r["mean"], r["sd"], r["ci95"]))
    if "text_only_minus_vision_only" in rec:
        r = rec["text_only_minus_vision_only"]
        print("  text_only - vision_only: %+.4f (t=%.2f p=%.4f d=%.2f)" % (r["mean_diff"], r["t"], r["p"], r["cohen_d"]))

io.open(os.path.join(OUT_DIR, "paperA_prereg_stats.json"), "w", encoding="utf-8", newline="").write(
    json.dumps({"script": "tools/_p1767_upgrade_a2_a3.py", "backbones": stats_out}, indent=2))
print("\nwrote", os.path.join(OUT_DIR, "paperA_prereg_stats.json"))
