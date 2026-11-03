# -*- coding: utf-8 -*-
r"""A1 Round-1 analyses: training-split margin selection, retrieval monitor, and epochs saved.

Output: outputs/analysis/a1_round1_analysis.json

    python tools/_p1434_a1_round1_analysis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_round1_analysis.json")


def load(name):
    p = os.path.join(REPO, "outputs", "analysis", name)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def regret(tops, idx):
    return max(tops) - tops[idx]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    out = {}

    # --- training-split margin selection vs held-out margin selection
    tm = load("a1_monitor_trainmass.json")
    if tm:
        per = {}
        for ds, rows in tm["runs"].items():
            tops = [r["eval_top1"] for r in rows]
            i_eval = int(np.argmin([r["eval_mass_0.01"] for r in rows]))
            i_train = int(np.argmin([r["train_mass_0.01"] for r in rows]))
            i_cg = int(np.argmin([r["eval_CG"] for r in rows]))
            per[ds] = {
                "oracle_epoch": int(np.argmax(tops)) + 1, "oracle_top1": max(tops),
                "eval_mass_epoch": i_eval + 1, "eval_mass_top1": tops[i_eval], "eval_mass_regret": regret(tops, i_eval),
                "train_mass_epoch": i_train + 1, "train_mass_top1": tops[i_train], "train_mass_regret": regret(tops, i_train),
                "min_cg_regret": regret(tops, i_cg),
                "last_regret": regret(tops, len(tops) - 1), "first_regret": regret(tops, 0),
            }
        rules = ["eval_mass_regret", "train_mass_regret", "min_cg_regret", "last_regret", "first_regret"]
        out["trainmass"] = {"per_run": per,
                            "summary": {r: {"mean": float(np.mean([per[k][r] for k in per])),
                                            "max": float(np.max([per[k][r] for k in per]))} for r in rules}}
    # --- retrieval monitor
    rm = load("a1_retrieval_monitor.json")
    if rm:
        rows = rm["runs"]["marine_retrieval"]
        tops = [r["R@1"] for r in rows]
        i_m1 = int(np.argmin([r["mass_0.01"] for r in rows]))
        i_cg = int(np.argmin([r["CG"] for r in rows]))
        out["retrieval"] = {
            "oracle_epoch": int(np.argmax(tops)) + 1, "oracle_R1": max(tops),
            "min_mass01_epoch": i_m1 + 1, "min_mass01_R1": tops[i_m1], "min_mass01_regret": regret(tops, i_m1),
            "min_cg_regret": regret(tops, i_cg),
            "last_regret": regret(tops, len(tops) - 1), "first_regret": regret(tops, 0),
            "epochs": len(rows),
        }
    # --- epochs saved from the diagnosis split
    diag = load("a1_monitor_diagnosis.json")
    if diag:
        per = diag["per_run"]

        def ds(k):
            for d in ("dtd", "food101", "fathomnet8", "inat_wild"):
                if d in k:
                    return d
        small = [k for k in per if ds(k) in ("fathomnet8", "inat_wild")]
        large = [k for k in per if k not in small]

        def stats(keys):
            saved = [10 - per[k]["epoch_first"] for k in keys]
            extra = [per[k]["regret_first"] - per[k]["regret_epoch_last_epoch"] for k in keys]
            return {"n": len(keys), "mean_epochs_saved": float(np.mean(saved)),
                    "mean_extra_regret_vs_last": float(np.mean(extra))}
        out["epochs_saved"] = {"large": stats(large), "small": stats(small)}

    print("  trainmass summary:", {k: round(v["mean"], 2) for k, v in out.get("trainmass", {}).get("summary", {}).items()})
    if "retrieval" in out:
        r = out["retrieval"]
        print(f"  retrieval: oracle ep{r['oracle_epoch']} R@1={r['oracle_R1']:.1f}; min-mass ep{r['min_mass01_epoch']} "
              f"R@1={r['min_mass01_R1']:.1f} regret={r['min_mass01_regret']:.1f}; last regret={r['last_regret']:.1f}")
    if "epochs_saved" in out:
        print("  epochs saved:", out["epochs_saved"])
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
