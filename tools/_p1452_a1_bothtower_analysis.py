# -*- coding: utf-8 -*-
r"""A1: analysis of the both-tower LoRA monitoring run.

Output: outputs/analysis/a1_monitor_bothtower_analysis.json

    python tools/_p1452_a1_bothtower_analysis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "outputs", "analysis", "a1_monitor_bothtower.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a1_monitor_bothtower_analysis.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(SRC):
        print("  both-tower archive not ready")
        return 0
    d = json.load(io.open(SRC, encoding="utf-8"))
    out = {"source": "outputs/analysis/a1_monitor_bothtower.json", "per_run": {}, "summary": {}}
    rules = {"mass": "mass_0.01", "cg": "CG"}
    for ds, rows in d["runs"].items():
        tops = [r["top1"] for r in rows]
        i_mass = int(np.argmin([r["mass_0.01"] for r in rows]))
        i_cg = int(np.argmin([r["CG"] for r in rows]))
        out["per_run"][ds] = {
            "oracle_epoch": int(np.argmax(tops)) + 1, "oracle_top1": max(tops),
            "mass_epoch": i_mass + 1, "mass_regret": max(tops) - tops[i_mass],
            "cg_regret": max(tops) - tops[i_cg],
            "first_regret": max(tops) - tops[0], "last_regret": max(tops) - tops[-1],
            "within_1pt_epochs": int(sum(1 for t in tops if max(tops) - t <= 1.0)),
        }
    keys = ("mass_regret", "cg_regret", "first_regret", "last_regret")
    out["summary"] = {k: {"mean": float(np.mean([out["per_run"][x][k] for x in out["per_run"]])),
                          "max": float(np.max([out["per_run"][x][k] for x in out["per_run"]]))} for k in keys}
    print("  summary:", {k: round(v["mean"], 2) for k, v in out["summary"].items()})
    for ds, r in out["per_run"].items():
        print(f"   {ds}: oracle ep{r['oracle_epoch']} top1={r['oracle_top1']:.1f} "
              f"mass_regret={r['mass_regret']:.1f} last={r['last_regret']:.1f}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
