# -*- coding: utf-8 -*-
r"""Workstream E, second pass: fit the four competing models to the archived alignment-energy trajectories
found in `outputs/llava_second_order_ode.json` (trajectories.<rank>.epochs/E) and `outputs/c3_log_dynamics.json`
(cells[i].epochs/E). Prints mean R^2 per model, per-model wins, and writes the ledger JSON.
"""
import glob
import io
import json
import os

import numpy as np
from scipy.optimize import curve_fit

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def collect():
    out = []

    def walk(o, tag):
        if isinstance(o, dict):
            ep = o.get("epochs") or o.get("epoch")
            ys = o.get("E") or o.get("energy") or o.get("dg") or o.get("CG")
            if isinstance(ep, list) and isinstance(ys, list) and len(ep) == len(ys) and len(ep) >= 4:
                try:
                    t = np.array([float(v) for v in ep])
                    y = np.array([float(v) for v in ys])
                    if np.all(np.isfinite(t)) and np.all(np.isfinite(y)):
                        out.append((tag, t, y))
                except Exception:
                    pass
            for k, v in o.items():
                walk(v, tag + "." + k)
        elif isinstance(o, list):
            for i, v in enumerate(o[:200]):
                walk(v, tag + "[%d]" % i)

    for p in ("outputs/llava_second_order_ode.json", "outputs/c3_log_dynamics.json"):
        if os.path.isfile(p):
            walk(json.load(io.open(p, encoding="utf-8")), os.path.basename(p))
    return out


def r2(y, yh):
    ss = float(((y - yh) ** 2).sum()); tot = float(((y - y.mean()) ** 2).sum())
    return 1.0 - ss / tot if tot > 0 else float("nan")


def aic(y, yh, k):
    n = len(y); ss = float(((y - yh) ** 2).sum())
    return n * np.log(ss / n + 1e-12) + 2 * k


def fit(t, y):
    r = {}
    r["constant"] = (np.full_like(y, y.mean()), 1)
    r["linear"] = (np.polyval(np.polyfit(t, y, 1), t), 2)
    try:
        p, _ = curve_fit(lambda tt, c, a, q: c + a * np.power(np.maximum(tt, 1e-9), q), t, y,
                         p0=[y[-1], y[0] - y[-1], 0.5], maxfev=40000)
        r["power"] = (p[0] + p[1] * np.power(np.maximum(t, 1e-9), p[2]), 3)
    except Exception:
        r["power"] = (np.full_like(y, np.nan), 3)
    try:
        p, _ = curve_fit(lambda tt, c, a, k: c + a * (1.0 - np.exp(-k * tt)), t, y,
                         p0=[y[-1], y[0] - y[-1], 0.5], maxfev=40000)
        r["ode"] = (p[0] + p[1] * (1.0 - np.exp(-p[2] * t)), 3)
    except Exception:
        r["ode"] = (np.full_like(y, np.nan), 3)
    return r


series = collect()
print("usable energy trajectories:", len(series))
rows = []
for tag, t, y in series:
    f = fit(t, y)
    row = {"series": tag, "n": len(t), "E0": float(y[0]), "Eend": float(y[-1])}
    for m, (yh, k) in f.items():
        row[m + "_r2"] = r2(y, yh)
        row[m + "_aic"] = aic(y, yh, k) if np.all(np.isfinite(yh)) else float("inf")
    rows.append(row)

names = ["constant", "linear", "power", "ode"]
print("%-46s %2s %s" % ("series", "n", "  ".join("%-9s" % m for m in names)))
for r in rows[:12]:
    print("%-46s %2d %s" % (r["series"][-46:], r["n"], "  ".join("%-9.4f" % r[m + "_r2"] for m in names)))
print()
for m in names:
    v = [r[m + "_r2"] for r in rows if np.isfinite(r[m + "_r2"])]
    wins = 0
    for r in rows:
        vals = [(r[x + "_r2"], x) for x in names if np.isfinite(r[x + "_r2"])]
        if vals and max(vals)[1] == m:
            wins += 1
    print("  %-9s meanR2=%.4f  n=%d  wins=%d" % (m, float(np.mean(v)) if v else float("nan"), len(v), wins))
io.open("outputs/analysis/paperA_competing_models.json", "w", encoding="utf-8", newline="").write(
    json.dumps({"script": "tools/_p1736_competing_models_e.py", "series": rows}, indent=2))
print("wrote outputs/analysis/paperA_competing_models.json")
