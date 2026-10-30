# -*- coding: utf-8 -*-
r"""Workstream E: is the ODE actually a better description of gap evolution than simpler curves?

Fits four competing models to the same archived trajectories, per run, with the same data points:
  M0 constant            y = c
  M1 linear              y = c + b t
  M2 power law           y = c + a t^p
  M3 saturating exp      y = c + a (1 - e^{-k t})        <- the paper's first-order ODE solution
Report only what the archives can support; if a run has fewer than four epochs it is skipped and counted.
"""
import glob
import io
import json
import os
import re

import numpy as np

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from scipy.optimize import curve_fit
except Exception:
    curve_fit = None


def series_from(obj):
    """Yield (label, t, y) for any list-like gap trajectory found in the archive."""
    out = []

    def walk(o, pre=""):
        if isinstance(o, dict):
            ts = o.get("epoch") or o.get("epochs") or o.get("t")
            ys = (o.get("dg") or o.get("DG") or o.get("gap") or o.get("dg_star")
                  or o.get("gap_trajectory") or o.get("trajectory"))
            if isinstance(ts, list) and isinstance(ys, list) and len(ts) == len(ys) and len(ts) >= 4:
                try:
                    t = np.array([float(v) for v in ts])
                    y = np.array([float(v) for v in ys])
                    out.append((pre or "run", t, y))
                    return
                except Exception:
                    pass
            for k, v in o.items():
                walk(v, pre + ("." + k if pre else k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, pre + ("[%d]" % i if False else ""))

    walk(obj)
    return out


def r2(y, yh):
    ss_res = float(((y - yh) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def ic_aic(y, yh, k):
    n = len(y)
    ss = float(((y - yh) ** 2).sum())
    return n * np.log(ss / n + 1e-12) + 2 * k


def fit_models(t, y):
    res = {}
    n = len(t)
    res["constant"] = (np.full_like(y, y.mean()), 1)
    bt = np.polyfit(t, y, 1)
    res["linear"] = (np.polyval(bt, t), 2)
    try:
        pl, _ = curve_fit(lambda tt, c, a, p: c + a * np.power(np.maximum(tt, 1e-9), p),
                          t, y, p0=[y[-1], y[0] - y[-1], 0.5], maxfev=20000)
        res["power"] = (pl[0] + pl[1] * np.power(np.maximum(t, 1e-9), pl[2]), 3)
    except Exception:
        res["power"] = (np.full_like(y, np.nan), 3)
    try:
        pe, _ = curve_fit(lambda tt, c, a, k: c + a * (1.0 - np.exp(-k * tt)),
                          t, y, p0=[y[-1], y[0] - y[-1], 0.5], maxfev=20000)
        res["ode"] = (pe[0] + pe[1] * (1.0 - np.exp(-pe[2] * t)), 3)
    except Exception:
        res["ode"] = (np.full_like(y, np.nan), 3)
    return res


rows = []
files = sorted(glob.glob("outputs/analysis/*.json"))
scanned = 0
for p in files:
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    scanned += 1
    for label, t, y in series_from(d):
        if len(t) < 4:
            continue
        if not np.all(np.isfinite(t)) or not np.all(np.isfinite(y)):
            continue
        fits = fit_models(t, y)
        row = {"file": os.path.basename(p), "series": label, "n": len(t)}
        for m, (yh, k) in fits.items():
            row[m + "_r2"] = r2(y, yh)
            row[m + "_aic"] = ic_aic(y, yh, k) if np.all(np.isfinite(yh)) else float("inf")
        rows.append(row)

print("json files scanned:", scanned, "| usable trajectory series:", len(rows))
if rows:
    names = ["constant", "linear", "power", "ode"]
    print("%-34s %-10s %3s %s" % ("file", "series", "n", "  ".join("%-9s" % m for m in names)))
    for r in rows[:14]:
        print("%-34s %-10s %3d %s" % (r["file"][:34], r["series"][-10:], r["n"],
                                      "  ".join("%-9.4f" % r[m + "_r2"] for m in names)))
    print()
    print("mean R2 by model:")
    for m in names:
        vals = [r[m + "_r2"] for r in rows if np.isfinite(r[m + "_r2"])]
        print("  %-9s mean R2 = %.4f  (n=%d, wins=%d)" % (
            m, float(np.mean(vals)) if vals else float("nan"), len(vals),
            sum(1 for r in rows if np.isfinite(r[m + "_r2"]) and r[m + "_r2"] == max(
                r[x + "_r2"] for x in names if np.isfinite(r[x + "_r2"])))))
    io.open("outputs/analysis/paperA_competing_models.json", "w", encoding="utf-8", newline="").write(
        json.dumps({"script": "tools/_p1735_competing_models.py", "runs": rows}, indent=2))
    print("wrote outputs/analysis/paperA_competing_models.json")
