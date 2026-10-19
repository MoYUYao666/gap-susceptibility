# -*- coding: utf-8 -*-
r"""Add the combined monitoring claims to the A1 ledger and insert the tau-calibration clause into A23.

    python tools/_p1400_ledger_and_calib.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import json

LEDGER = "tools/_claim_ledger_a1.py"
A23TEX = "paper_a2/ext_partII_domains.tex"
CALIB = "outputs/analysis/a23_tau_calibration.json"
BLOCK = '''    # ---- expanded-set monitoring comparison (extra seeds + fourth domain)
    comb = load("outputs/analysis/a1_monitor_combined.json")
    _r = comb["rules"]
    claim("combined runs", 20, comb["n_runs"], "...a1_monitor_combined", 0)
    claim("combined checkpoints", 200, comb["correlation"]["n_checkpoints"], "...a1_monitor_combined", 0)
    claim("combined min-M mean regret", 1.70, _r["minM"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined min-M max regret", 10.00, _r["minM"]["max_regret"], "...a1_monitor_combined", 2)
    claim("combined last-epoch mean regret", 1.32, _r["last"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined first-epoch mean regret", 7.25, _r["first"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined sequential mean regret", 3.82, _r["seqM"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined entropy mean regret", 1.91, _r["minEntropy"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined max-softmax mean regret", 2.26, _r["maxSoftmax"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined max-logit mean regret", 3.91, _r["maxLogit"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined energy mean regret", 3.74, _r["minEnergy"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined pooled r(M)", -0.977, comb["correlation"]["pooled_M"], "...a1_monitor_combined", 3)

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(LEDGER, encoding="utf-8").read()
    if "expanded-set monitoring comparison" not in t:
        anchor = "    # ---- epoch sweep correlation (manuscript abstract/intro/epoch subsection)"
        assert t.count(anchor) == 1
        t = t.replace(anchor, BLOCK + anchor, 1)
        print("  ledger block added")
    else:
        print("  ledger block already present")
    if a.apply:
        io.open(LEDGER, "w", encoding="utf-8", newline="").write(t)
        ast.parse(io.open(LEDGER, encoding="utf-8").read())

    d = json.load(io.open(CALIB, encoding="utf-8"))
    lin = d["linear"]
    sp = [v["test_spearman"] for v in lin.values()]
    pe = [v["test_pearson"] for v in lin.values()]
    maes = [v["test_MAE"] for v in lin.values()]
    clause = (f" After a linear rescaling fitted on one encoder, $\\tau$'s accuracy relation transfers to the other "
              f"(Spearman ${min(sp):+.2f}$--${max(sp):+.2f}$, Pearson ${min(pe):+.2f}$--${max(pe):+.2f}$, mean absolute "
              f"error ${min(maes):.1f}$--${max(maes):.1f}$ accuracy points), although a hard threshold still does not "
              f"(balanced accuracy $0.38$--$0.50$); the ordering transfers up to a monotone rescaling, the scale does not.")
    tex = io.open(A23TEX, encoding="utf-8").read()
    if "After a linear rescaling fitted on one encoder" not in tex:
        anchor = "diagnostic the framework actually uses."
        assert tex.count(anchor) == 1
        tex = tex.replace(anchor, anchor + clause, 1)
        print("  A23 calibration clause inserted")
    else:
        print("  A23 clause already present")
    if a.apply:
        io.open(A23TEX, "w", encoding="utf-8", newline="").write(tex)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
