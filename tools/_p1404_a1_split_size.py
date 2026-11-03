# -*- coding: utf-8 -*-
r"""A1: stratify the monitoring diagnosis by held-out size.

The expanded-set reversal is concentrated on the two small held-out splits. This script converts every regret into units of
the binomial standard error of the held-out accuracy, so the diagnosis is stated in sampling terms rather than as a
property of the statistic.

Output: outputs/analysis/a1_monitor_split_diagnosis.json

    python tools/_p1404_a1_split_size.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAG = os.path.join(REPO, "outputs", "analysis", "a1_monitor_diagnosis.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a1_monitor_split_diagnosis.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(DIAG, encoding="utf-8"))
    rows = {}
    for key, v in d["per_run"].items():
        step = v["quant_step"]
        n_eval = round(1 / step) if step else None
        p = v["oracle_top1"] / 100.0
        se = 100.0 * math.sqrt(p * (1 - p) / n_eval) if n_eval else None
        rows[key] = {"dataset": v["dataset"], "n_eval": n_eval, "se_points": round(se, 2) if se else None,
                     "regret_minM": v["regret_first"], "regret_last": v["regret_epoch_last_epoch"],
                     "regret_first_epoch": v["regret_first_epoch"],
                     "regret_minM_in_SE": round(v["regret_first"] / se, 2) if se else None}
    groups = {"small": [k for k, v in rows.items() if v["dataset"] in ("fathomnet8", "inat_wild")],
              "large": [k for k, v in rows.items() if v["dataset"] in ("dtd", "food101")]}
    summary = {}
    for g, keys in groups.items():
        summary[g] = {
            "n_runs": len(keys),
            "n_eval_range": [min(rows[k]["n_eval"] for k in keys), max(rows[k]["n_eval"] for k in keys)],
            "mean_regret_minM": float(np.mean([rows[k]["regret_minM"] for k in keys])),
            "mean_regret_last_epoch": float(np.mean([rows[k]["regret_last"] for k in keys])),
            "mean_regret_first_epoch": float(np.mean([rows[k]["regret_first_epoch"] for k in keys])),
            "mean_regret_minM_in_SE": float(np.mean([rows[k]["regret_minM_in_SE"] for k in keys])),
        }
    print("  small splits:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in summary["small"].items()})
    print("  large splits:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in summary["large"].items()})
    out = {"summary": summary, "per_run": rows}
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
