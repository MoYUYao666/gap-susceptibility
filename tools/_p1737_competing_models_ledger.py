# -*- coding: utf-8 -*-
r"""Workstream E, third pass: use the ledger the manuscript itself cites (`outputs/analysis/ode_ledger.json`),
which holds one record per archived run, and compare the four candidate descriptions of the trajectory:
constant, linear, power law, and the bounded saturating exponential (the ODE solution, k bounded away from 0 so the
fit cannot degenerate into a line). Writes outputs/analysis/paperA_competing_models.json.
"""
import io
import json
import os

import numpy as np
from scipy.optimize import curve_fit

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
L = json.load(io.open("outputs/analysis/ode_ledger.json", encoding="utf-8"))
runs = L["runs"]
print("ledger runs:", len(runs), "| one record keys:", sorted(runs[0])[:14])


def series_of(r):
    for tk in ("epochs", "epoch", "eps"):
        if isinstance(r.get(tk), list):
            t = np.array([float(v) for v in r[tk]])
            for yk in ("cg", "CG", "dg", "DG", "dg_star", "gap", "traj"):
                if isinstance(r.get(yk), list) and len(r[yk]) == len(t):
                    y = np.array([float(v) for v in r[yk]])
                    if np.all(np.isfinite(t)) and np.all(np.isfinite(y)):
                        return t, y
    return None, None


series = []
for r in runs:
    t, y = series_of(r)
    if t is not None and len(t) >= 4:
        series.append((r.get("name") or r.get("run") or r.get("arm") or "run", t, y))
print("runs with a usable trajectory:", len(series))


def r2(y, yh):
    ss = float(((y - yh) ** 2).sum()); tot = float(((y - y.mean()) ** 2).sum())
    return 1.0 - ss / tot if tot > 0 else float("nan")


def aic(y, yh, k):
    n = len(y); ss = float(((y - yh) ** 2).sum())
    return n * np.log(ss / n + 1e-12) + 2 * k


def fit(t, y):
    r = {"constant": (np.full_like(y, y.mean()), 1)}
    r["linear"] = (np.polyval(np.polyfit(t, y, 1), t), 2)
    try:
        p, _ = curve_fit(lambda tt, c, a, q: c + a * np.power(np.maximum(tt, 1e-9), q), t, y,
                         p0=[y[-1], y[0] - y[-1], 0.5], maxfev=60000)
        r["power"] = (p[0] + p[1] * np.power(np.maximum(t, 1e-9), p[2]), 3)
    except Exception:
        r["power"] = (np.full_like(y, np.nan), 3)
    try:
        p, _ = curve_fit(lambda tt, c, a, k: c + a * (1.0 - np.exp(-k * tt)), t, y,
                         p0=[y[-1], y[0] - y[-1], 0.5],
                         bounds=([-np.inf, -np.inf, 1e-3], [np.inf, np.inf, 10.0]), maxfev=60000)
        r["ode"] = (p[0] + p[1] * (1.0 - np.exp(-p[2] * t)), 3)
    except Exception:
        r["ode"] = (np.full_like(y, np.nan), 3)
    return r


rows = []
for tag, t, y in series:
    f = fit(t, y)
    row = {"series": str(tag)[:40], "n": len(t)}
    for m, (yh, k) in f.items():
        row[m + "_r2"] = r2(y, yh)
        row[m + "_aic"] = aic(y, yh, k) if np.all(np.isfinite(yh)) else float("inf")
    rows.append(row)

names = ["constant", "linear", "power", "ode"]
if rows:
    print("\n%-34s %2s %s" % ("series", "n", "  ".join("%-9s" % m for m in names)))
    for r in rows[:10]:
        print("%-34s %2d %s" % (r["series"][-34:], r["n"], "  ".join("%-9.4f" % r[m + "_r2"] for m in names)))
    print()
    for m in names:
        v = [r[m + "_r2"] for r in rows if np.isfinite(r[m + "_r2"])]
        wins = sum(1 for r in rows if np.isfinite(r[m + "_r2"]) and
                   max((r[x + "_r2"], x) for x in names if np.isfinite(r[x + "_r2"]))[1] == m)
        print("  %-9s meanR2=%.4f  n=%d  wins=%d" % (m, float(np.mean(v)) if v else float("nan"), len(v), wins))
io.open("outputs/analysis/paperA_competing_models.json", "w", encoding="utf-8", newline="").write(
    json.dumps({"script": "tools/_p1737_competing_models_ledger.py", "series": rows}, indent=2))
print("wrote outputs/analysis/paperA_competing_models.json")
