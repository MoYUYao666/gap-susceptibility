# -*- coding: utf-8 -*-
r"""Evaluate a tau-based monitoring protocol on the archived per-epoch trajectories.

The manuscript claims that the Kendall order statistic tau tracks zero-shot accuracy and is cheap (it needs only the
top-k sets a validation pass already produces). A claim about tracking is not yet a usable protocol. This script turns it
into one and reports its operating characteristics on every archived trajectory:

  rules      argmax-tau        stop at the epoch with the largest tau
             patience-2        stop at the first epoch whose tau has fallen for two consecutive epochs
             cusum             stop when the one-sided CUSUM of standardized tau decrements exceeds h
             last-epoch        stop at the final epoch (no monitoring)
             first-epoch       stop at epoch 1 (no monitoring)
  oracle     the epoch with the largest measured top-1

For each rule and trajectory: selected epoch, selected top-1, regret against the oracle, and lead relative to the epoch
where top-1 peaks. The CUSUM threshold is calibrated leave-one-trajectory-out so its in-sample false-alarm budget is
reported honestly rather than tuned on the same points it is scored on.

Input : outputs/a1_epoch_sweep.json   (10 trajectories x 10 epochs; tau5 and top1_5k)
Output: outputs/analysis/a1_monitor_protocol.json

    python tools/_p1255_tau_monitor_protocol.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "outputs", "a1_epoch_sweep.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a1_monitor_protocol.json")


def load_trajectories():
    d = json.load(open(SRC, encoding="utf-8"))
    traj = {}
    for c in d["checkpoints"]:
        key = "%s|seed%s" % (c["dataset"], c["seed"])
        traj.setdefault(key, []).append(c)
    out = {}
    for k, rows in traj.items():
        rows = sorted(rows, key=lambda r: r["epoch"])
        tau = np.asarray([r["tau5"] for r in rows], dtype=float)
        top1 = np.asarray([r.get("top1_5k", r.get("top1")) for r in rows], dtype=float)
        epochs = np.asarray([r["epoch"] for r in rows], dtype=int)
        out[k] = {"epochs": epochs, "tau": tau, "top1": top1}
    return out


def cusum_alarm(tau: np.ndarray, h: float, kappa: float = 0.5):
    """One-sided CUSUM on standardized decrements; returns the 0-based index of the first alarm or None."""
    d = np.diff(tau)
    if len(d) == 0:
        return None
    sd = np.std(d, ddof=1) if len(d) > 1 else 1e-9
    sd = max(sd, 1e-9)
    s = 0.0
    for i, di in enumerate(d):
        s = max(0.0, s - di / sd - kappa)
        if s > h:
            return i + 1
    return None


def patience_stop(tau: np.ndarray, patience: int = 2):
    best, run = 0, 0
    for i in range(1, len(tau)):
        if tau[i] < tau[i - 1] - 1e-12:
            run += 1
            if run >= patience:
                return i - patience + 1
        else:
            run = 0
            if tau[i] > tau[best]:
                best = i
    return best


def evaluate(traj, h):
    rows, fa_total, fa_steps = [], 0, 0
    for key, t in traj.items():
        tau, top1 = t["tau"], t["top1"]
        oracle_i = int(np.argmax(top1))
        picks = {
            "oracle": oracle_i,
            "argmax_tau": int(np.argmax(tau)),
            "patience2": patience_stop(tau, 2),
            "first_epoch": 0,
            "last_epoch": len(tau) - 1,
        }
        alarm = cusum_alarm(tau, h)
        picks["cusum"] = alarm if alarm is not None else 0
        for rule, i in picks.items():
            rows.append({"trajectory": key, "rule": rule, "epoch": int(t["epochs"][i]),
                         "top1": float(top1[i]), "regret_vs_oracle": float(top1[oracle_i] - top1[i]),
                         "lead_vs_oracle_epoch": int(t["epochs"][oracle_i] - t["epochs"][i]),
                         "tau": float(tau[i])})
        # false alarms for the CUSUM: an alarm when top-1 is not meaningfully below its trajectory maximum
        if alarm is not None:
            fa_steps += 1
            if top1[alarm] >= top1[oracle_i] - 0.5:
                fa_total += 1
    summary = {}
    for rule in ("oracle", "argmax_tau", "patience2", "cusum", "last_epoch", "first_epoch"):
        sub = [r for r in rows if r["rule"] == rule]
        summary[rule] = {"mean_top1": float(np.mean([r["top1"] for r in sub])),
                         "mean_regret": float(np.mean([r["regret_vs_oracle"] for r in sub])),
                         "max_regret": float(np.max([r["regret_vs_oracle"] for r in sub])),
                         "mean_epoch": float(np.mean([r["epoch"] for r in sub]))}
    return rows, summary, {"cusum_alarms": fa_steps, "cusum_false_alarms": fa_total}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    traj = load_trajectories()
    n = len(traj)
    print(f"  trajectories: {n} ({', '.join(sorted(traj))})")

    # calibrate h by leave-one-out: for each held-out trajectory, pick the smallest h that gives no alarm on the others
    hs = np.round(np.arange(0.5, 6.01, 0.25), 2)
    loo = []
    for key in sorted(traj):
        others = {k: v for k, v in traj.items() if k != key}
        h_sel = hs[-1]
        for h in hs:
            alarms = sum(1 for v in others.values() if cusum_alarm(v["tau"], h) is not None)
            if alarms == 0:
                h_sel = h
                break
        loo.append(float(h_sel))
    h_med = float(np.median(loo))
    print(f"  LOO-calibrated CUSUM thresholds: median={h_med} min={min(loo)} max={max(loo)}")

    rows, summary, fa = evaluate(traj, h_med)
    print("\n  rule            mean top-1   mean regret   max regret   mean epoch")
    for rule, s in summary.items():
        print(f"  {rule:<14} {s['mean_top1']:>10.2f} {s['mean_regret']:>13.2f} {s['max_regret']:>12.2f} {s['mean_epoch']:>12.2f}")
    print(f"  CUSUM alarms={fa['cusum_alarms']} false={fa['cusum_false_alarms']} (h={h_med})")

    payload = {"source": "outputs/a1_epoch_sweep.json", "n_trajectories": n,
               "rules": {"argmax_tau": "stop at the epoch of maximum tau",
                         "patience2": "stop when tau has fallen for two consecutive epochs",
                         "cusum": "stop when one-sided CUSUM of standardized tau decrements exceeds h",
                         "first_epoch": "stop after epoch 1 (no monitoring)",
                         "last_epoch": "stop at the final epoch (no monitoring)",
                         "oracle": "epoch of maximum measured top-1 (upper bound)"},
               "cusum": {"kappa": 0.5, "h_median_loo": h_med, "h_loo_per_trajectory": loo,
                         "in_sample_alarms": fa["cusum_alarms"], "in_sample_false_alarms": fa["cusum_false_alarms"],
                         "false_alarm_definition": "alarm epoch whose top-1 is within 0.5 point of the trajectory maximum"},
               "summary": summary, "rows": rows,
               "caveat": "ten trajectories from one training family; top-1 is measured on a fixed 5,000-image holdout, "
                         "so the regret-optimal epoch is known only post hoc"}
    if a.apply:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("\n  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
