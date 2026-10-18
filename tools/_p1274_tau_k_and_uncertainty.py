# -*- coding: utf-8 -*-
r"""Item C: how large must k be in the top-k order statistic?  Item E: uncertainty of the monitoring regret.

C  `a1_prompt_template_gap.json` stores tau at k = 5 and k = 10 for every template and backbone. This script reports the
   mean difference and whether the two k values rank the templates the same way; if they do, k = 5 is enough and the
   cheaper statistic is the right default.
E  `a1_monitor_protocol.json` stores per-trajectory regrets for every selection rule. Ten trajectories are few, so this
   script bootstraps over trajectories to put an interval on the mean regret of each rule and on the paired advantage of
   the tau-max rule over training to the last epoch.

Outputs: outputs/analysis/a1_tau_k.json, outputs/analysis/a1_monitor_uncertainty.json

    python tools/_p1274_tau_k_and_uncertainty.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
from collections import defaultdict

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")


def tau_k():
    d = json.load(io.open(os.path.join(AN, "a1_prompt_template_gap.json"), encoding="utf-8"))
    from scipy import stats
    out = {"backbones": {}}
    for tag, v in d["models"].items():
        pairs = [(r["tau5"], r["tau10"]) for r in v["rows"] if r["tau5"] is not None and r["tau5"] < 0.999]
        if not pairs:
            continue
        t5 = [p[0] for p in pairs]
        t10 = [p[1] for p in pairs]
        rho = float(stats.spearmanr(t5, t10)[0]) if len(set(t5)) > 1 else 1.0
        out["backbones"][tag] = {"n_templates": len(pairs),
                                 "mean_tau5": float(np.mean(t5)), "mean_tau10": float(np.mean(t10)),
                                 "mean_gain_k10_minus_k5": float(np.mean(np.array(t10) - np.array(t5))),
                                 "spearman_k5_vs_k10": rho,
                                 "min_tau5": float(np.min(t5)), "min_tau10": float(np.min(t10))}
    t5s = [v["mean_tau5"] for v in out["backbones"].values()]
    t10s = [v["mean_tau10"] for v in out["backbones"].values()]
    out["summary"] = {"n_backbones": len(t5s), "mean_tau5": float(np.mean(t5s)), "mean_tau10": float(np.mean(t10s)),
                      "mean_gain": float(np.mean(np.array(t10s) - np.array(t5s))),
                      "min_spearman": float(min(v["spearman_k5_vs_k10"] for v in out["backbones"].values()))}
    return out


def monitor_uncertainty(n_boot=5000, seed=0):
    d = json.load(io.open(os.path.join(AN, "a1_monitor_protocol.json"), encoding="utf-8"))
    per = defaultdict(list)
    for r in d["rows"]:
        per[r["rule"]].append((r["trajectory"], r["regret_vs_oracle"]))
    traj = sorted({t for v in per.values() for t, _ in v})
    print(f"  trajectories: {len(traj)}")
    table = {}
    for rule, rows in per.items():
        m = {t: g for t, g in rows}
        vals = np.array([m[t] for t in traj])
        rs = np.random.RandomState(seed)
        boots = [vals[rs.randint(0, len(vals), len(vals))].mean() for _ in range(n_boot)]
        table[rule] = {"mean": float(vals.mean()), "ci95": [float(np.percentile(boots, 2.5)),
                                                           float(np.percentile(boots, 97.5))]}
    # paired advantage of tau-max over last-epoch
    tm = {t: g for t, g in per["argmax_tau"]}
    le = {t: g for t, g in per["last_epoch"]}
    diff = np.array([le[t] - tm[t] for t in traj])
    rs = np.random.RandomState(seed + 1)
    boots = [diff[rs.randint(0, len(diff), len(diff))].mean() for _ in range(n_boot)]
    return {"n_trajectories": len(traj), "rules": table,
            "tau_max_advantage_over_last": {"mean": float(diff.mean()),
                                            "ci95": [float(np.percentile(boots, 2.5)),
                                                     float(np.percentile(boots, 97.5))]}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    k = tau_k()
    print("  tau@k summary:", json.dumps(k["summary"], indent=1))
    for tag, v in k["backbones"].items():
        print(f"   {tag:<10} mean tau5={v['mean_tau5']:.3f} tau10={v['mean_tau10']:.3f} "
              f"gain={v['mean_gain_k10_minus_k5']:+.3f} rank corr={v['spearman_k5_vs_k10']:.3f}")
    u = monitor_uncertainty()
    print("  monitor regret (95% CI):")
    for rule, v in u["rules"].items():
        print(f"   {rule:<12} {v['mean']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]")
    print("  tau-max advantage over last epoch:", u["tau_max_advantage_over_last"])
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(os.path.join(AN, "a1_tau_k.json"), "w", encoding="utf-8", newline="").write(json.dumps(k, indent=1))
    io.open(os.path.join(AN, "a1_monitor_uncertainty.json"), "w", encoding="utf-8", newline="").write(json.dumps(u, indent=1))
    print("  wrote a1_tau_k.json and a1_monitor_uncertainty.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
