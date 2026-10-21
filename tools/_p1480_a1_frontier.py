# -*- coding: utf-8 -*-
r"""A1: compute the risk-compute frontier of the sequential margin-mass stopping rule.

Combines the per-epoch monitoring archives (interior, interior_extra, interior_v2), keeps the large-holdout runs, and for a
grid of trigger margins eps reports the mean accuracy regret and mean epochs saved of the sequential rule
(stop at the first epoch whose mass rises eps above the running minimum; keep the running-minimum checkpoint).

Output: outputs/analysis/a1_monitor_frontier.json

    python tools/_p1480_a1_frontier.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_monitor_frontier.json")
FILES = ["outputs/analysis/a1_monitor_interior.json", "outputs/analysis/a1_monitor_interior_extra.json",
         "outputs/analysis/a1_monitor_interior_v2.json"]
EPS = [0.005, 0.01, 0.02, 0.05]


def load_runs():
    runs = {}
    for rel in FILES:
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            continue
        d = json.load(io.open(p, encoding="utf-8"))
        for key, rows in d.get("runs", {}).items():
            tag = key
            if tag in runs:
                tag = rel.split("/")[-1] + "::" + key
            runs[tag] = {"rows": rows, "small": ("fathomnet8" in key or "inat" in key)}
    return runs


def rule(rows, eps):
    mass = [r["mass_0.01"] for r in rows]
    top = [r["top1"] for r in rows]
    best_i = 0
    stop = len(rows)
    for t in range(1, len(rows)):
        if mass[t] > mass[best_i] + eps:
            stop = t + 1
            break
        if mass[t] < mass[best_i]:
            best_i = t
    return {"selected_epoch": best_i + 1, "stop_epoch": stop,
            "selected_top1": top[best_i], "oracle_top1": max(top),
            "regret": max(top) - top[best_i], "epochs_saved": len(rows) - stop}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    runs = load_runs()
    large = {k: v for k, v in runs.items() if not v["small"]}
    small = {k: v for k, v in runs.items() if v["small"]}
    out = {"n_large_runs": len(large), "n_small_runs": len(small), "eps_grid": EPS, "rules": {}}
    for eps in EPS:
        res = [rule(v["rows"], eps) for v in large.values()]
        out["rules"][str(eps)] = {
            "mean_regret": float(np.mean([r["regret"] for r in res])),
            "max_regret": float(np.max([r["regret"] for r in res])),
            "mean_epochs_saved": float(np.mean([r["epochs_saved"] for r in res])),
            "frac_regret_le_0.5": float(np.mean([r["regret"] <= 0.5 for r in res])),
        }
    fine = [rule(v["rows"], 0.01) for v in large.values()]
    out["per_run_eps_0.01"] = {k: rule(v["rows"], 0.01) for k, v in large.items()}
    out["small_holdouts_note"] = {
        "n": len(small), "mean_regret_eps_0.01": (float(np.mean([rule(v["rows"], 0.01)["regret"] for v in small.values()]))
                                                  if small else None)}
    print(f"  large runs: {len(large)}, small runs: {len(small)}")
    for eps in EPS:
        r = out["rules"][str(eps)]
        print(f"  eps={eps:<5}: mean_regret={r['mean_regret']:.2f} max={r['max_regret']:.2f} "
              f"saved={r['mean_epochs_saved']:.1f} frac<=0.5={r['frac_regret_le_0.5']:.2f}")
    print("  small-holdout eps=0.01:", out["small_holdouts_note"])
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
