#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p448_p3_nan_diagnostics.py -- P3 review item R3.22 (offline part).

"The paper interprets NaN outputs at high rank as genuine representational
 collapse; provide diagnostics of the model weights, activations, gradients, or
 loss trajectories to distinguish representational collapse from numerical
 instability associated with quantization, optimizer settings, or mixed
 precision."

Offline evidence available in this repository (no GPU needed):
  * every archived P3 training log carries a per-epoch task-loss trajectory and,
    for the newer runs, per-epoch routed gradient norms (||g|| vis / proj / llm);
  * the archived E trajectories give E(t) per epoch up to the NaN.

This script parses ALL of them and answers the decisive question:

  did the TASK LOSS stay finite (and even improve) while E became NaN?
     -> then the optimizer is not diverging; the non-finiteness enters through
        the alignment-energy measurement / representation path
  did the TASK LOSS itself diverge to NaN/0 and the gradient norms blow up?
     -> then this is numerical divergence (instability), not representational
        collapse

Output: outputs/analysis/p3_nan_diagnostics.json
"""
import glob
import json
import math
import os
import re
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "outputs", "analysis")

LOGDIRS = [os.path.join(ROOT, "outputs"), os.path.join(ROOT, "outputs", "logs"),
           os.path.join(ROOT, "paper3", "scripts", "outputs", "logs")]

RE_EPOCH_LOSS = re.compile(r"Epoch\s+(\d+):\s+avg_loss=([-\d.eE+nan]+)\s*\((\d+)/(\d+) valid\)"
                           r"(?:\s*\|\s*\|\|g\|\|\s*vis=([-\d.eE+nan]+)\s*proj=([-\d.eE+nan]+)\s*llm=([-\d.eE+nan]+))?")
RE_E_T = re.compile(r"E\((\d+)\)\s*=\s*([-\d.eE+nan]+)")
RE_STEP_LOSS = re.compile(r"step\s+(\d+)/(\d+)\s+loss=([-\d.eE+nan]+)")


def f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


logs = []
for d in LOGDIRS:
    if os.path.isdir(d):
        logs += sorted(glob.glob(os.path.join(d, "*.log")))
logs = sorted(set(logs))

runs = []
for p in logs:
    try:
        txt = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    epochs = []
    for m in RE_EPOCH_LOSS.finditer(txt):
        epochs.append({"epoch": int(m.group(1)), "avg_loss": f(m.group(2)),
                       "n_valid": int(m.group(3)), "n_total": int(m.group(4)),
                       "gradnorm_vis": f(m.group(5)), "gradnorm_proj": f(m.group(6)),
                       "gradnorm_llm": f(m.group(7))})
    E = [{"epoch": int(m.group(1)), "E": f(m.group(2))} for m in RE_E_T.finditer(txt)]
    steps = [{"step": int(m.group(1)), "loss": f(m.group(3))}
             for m in RE_STEP_LOSS.finditer(txt)]
    if not epochs and not E:
        continue
    run = {
        "log": os.path.relpath(p, ROOT),
        "n_epoch_records": len(epochs),
        "n_E_records": len(E),
        "n_step_records": len(steps),
        "epochs": epochs,
        "E_series": E,
        "E_first_finite": next((x["E"] for x in E if x["E"] is not None), None),
        "E_first_nan_epoch": next((x["epoch"] for x in E if x["E"] is None), None),
        "loss_first_nan_epoch": next((x["epoch"] for x in epochs if x["avg_loss"] is None), None),
        "loss_all_finite": all(x["avg_loss"] is not None for x in epochs) if epochs else None,
        "grad_all_finite": all(None not in (x["gradnorm_vis"], x["gradnorm_llm"])
                               for x in epochs) if epochs else None,
        "max_gradnorm_llm": max([x["gradnorm_llm"] for x in epochs
                                 if x["gradnorm_llm"] is not None], default=None),
        "max_gradnorm_vis": max([x["gradnorm_vis"] for x in epochs
                                 if x["gradnorm_vis"] is not None], default=None),
        "step_loss_all_finite": (all(s["loss"] is not None for s in steps) if steps else None),
        "min_step_loss": min([s["loss"] for s in steps if s["loss"] is not None], default=None),
        "max_step_loss": max([s["loss"] for s in steps if s["loss"] is not None], default=None),
    }
    runs.append(run)

# --- decisive cross-tabulation: runs where E goes NaN but the loss does not
nan_runs = [r for r in runs if r["E_first_nan_epoch"] is not None]
ctrl = {
    "n_logs_with_metrics": len(runs),
    "n_runs_where_E_becomes_nan": len(nan_runs),
    "n_runs_where_E_nan_BUT_loss_stays_finite": sum(
        1 for r in nan_runs if r["loss_all_finite"] and r["loss_first_nan_epoch"] is None),
    "n_runs_where_loss_also_becomes_nan": sum(
        1 for r in nan_runs if r["loss_first_nan_epoch"] is not None),
    "n_runs_with_zero_valid_steps": sum(
        1 for r in runs if any(e["n_valid"] == 0 for e in r["epochs"])),
}
ctrl["runs"] = [{
    "log": r["log"], "E_first_nan_epoch": r["E_first_nan_epoch"],
    "loss_first_nan_epoch": r["loss_first_nan_epoch"],
    "loss_all_finite": r["loss_all_finite"],
    "grad_all_finite": r["grad_all_finite"],
    "max_gradnorm_llm": r["max_gradnorm_llm"],
    "max_gradnorm_vis": r["max_gradnorm_vis"],
    "E_series": [(x["epoch"], x["E"]) for x in r["E_series"]],
    "loss_series": [(x["epoch"], x["avg_loss"], x["n_valid"], x["n_total"]) for x in r["epochs"]],
} for r in nan_runs]

# --- how does the loss behave right before the E NaN?
pre = []
for r in nan_runs:
    k = r["E_first_nan_epoch"]
    ls = [x for x in r["epochs"] if x["epoch"] == k - 1]
    if ls:
        pre.append({"log": r["log"], "nan_epoch": k,
                    "loss_prev_epoch": ls[0]["avg_loss"],
                    "n_valid_prev": ls[0]["n_valid"], "n_total_prev": ls[0]["n_total"],
                    "gradnorm_llm_prev": ls[0]["gradnorm_llm"],
                    "gradnorm_vis_prev": ls[0]["gradnorm_vis"],
                    "E_prev": next((x["E"] for x in r["E_series"] if x["epoch"] == k - 1), None)})
ctrl["loss_behaviour_immediately_before_E_nan"] = pre

# --- which logs have per-epoch gradient norms at all (for the paper's claim set)
have_gn = [r["log"] for r in runs if r["max_gradnorm_llm"] is not None]
ctrl["logs_with_per_epoch_grad_norms"] = have_gn
ctrl["n_logs_with_per_epoch_grad_norms"] = len(have_gn)

out = {"meta": {"script": "tools/_p448_p3_nan_diagnostics.py",
                "task": "task-11 (P3 R3.22, offline evidence)",
                "log_dirs_scanned": [os.path.relpath(d, ROOT) for d in LOGDIRS if os.path.isdir(d)],
                "n_logs_scanned": len(logs)},
       "nan_vs_loss_crosstab": ctrl,
       "all_runs": runs}
dst = os.path.join(OUTDIR, "p3_nan_diagnostics.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False)

print("logs scanned:", len(logs), " with metrics:", len(runs))
print(json.dumps(ctrl, indent=1, default=str)[:4000])
print("\nwrote", dst)
