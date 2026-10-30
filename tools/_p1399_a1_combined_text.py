# -*- coding: utf-8 -*-
r"""A1: add the expanded-set monitoring evidence honestly.

The expanded set (extra seeds + a fourth domain) weakens the earlier ranking: the minimum-mass rule is close to the oracle
but not uniformly better than training to the end. The sentences added here report both results rather than the favourable
subset only.

    python tools/_p1399_a1_combined_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

MAIN = "paper_a1/main.tex"
JSON = "outputs/analysis/a1_monitor_combined.json"
INTRO_ANCHOR = "\\end{itemize}\n\nThe paper also turns the argument into two operati"
PARA_ANCHOR = "the way accuracy does."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    r = d["rules"]
    c = d["correlation"]
    n_runs, n_ck = d["n_runs"], c["n_checkpoints"]
    conf = [r[k]["mean_regret"] for k in ("minEntropy", "maxSoftmax", "maxLogit", "minEnergy")]
    intro = ("\n\nOn the monitoring side, the margin mass ranks held-out checkpoints closely enough to support epoch\n"
             "selection: across %d trajectories (%d checkpoints) from DTD, Food-101, FathomNet and iNaturalist, the\n"
             "minimum-mass rule lands $%.2f$ points (mean) from the labelled oracle, against $%.2f$ for the first epoch\n"
             "and $%.2f$--$%.2f$ for confidence-based selection, although training to the end reaches $%.2f$." % (
                 n_runs, n_ck, r["minM"]["mean_regret"], r["first"]["mean_regret"], min(conf), max(conf),
                 r["last"]["mean_regret"]))
    para = (" Extending this comparison with two further seeds (44, 45) and a fourth held-out domain (inat\\_wild, species)\n"
            "gives %d checkpoints and a mixed result that we report as it stands: the minimum-mass rule costs $%.2f$ points\n"
            "(worst $%.2f$) against $%.2f$ (worst $%.2f$) for training to the end and $%.2f$ for the first epoch, while the\n"
            "sequential variant is unstable across domains ($%.2f$, worst $%.2f$) and confidence-based selection costs\n"
            "$%.2f$--$%.2f$. The rule is therefore close to the oracle and better than confidence selection, but it is not\n"
            "uniformly better than training to the end once the domain set widens; we keep the claim at the level of an\n"
            "in-domain selection statistic rather than a universally superior stopping rule." % (
                n_ck, r["minM"]["mean_regret"], r["minM"]["max_regret"], r["last"]["mean_regret"],
                r["last"]["max_regret"], r["first"]["mean_regret"], r["seqM"]["mean_regret"], r["seqM"]["max_regret"],
                min(conf), max(conf)))
    t = io.open(MAIN, encoding="utf-8").read()
    if "On the monitoring side, the margin mass ranks" in t:
        print("  already inserted")
    else:
        assert t.count(INTRO_ANCHOR) == 1, t.count(INTRO_ANCHOR)
        t = t.replace(INTRO_ANCHOR, "\\end{itemize}" + intro + "\n\nThe paper also turns the argument into two operati", 1)
        assert t.count(PARA_ANCHOR) == 1, t.count(PARA_ANCHOR)
        t = t.replace(PARA_ANCHOR, PARA_ANCHOR + para, 1)
        print("  intro and paragraph sentences inserted")
    for rule in ("minM", "seqM", "minCG", "maxSoftmax", "maxLogit", "minEntropy", "minEnergy", "first", "last"):
        print("  %-10s mean=%.2f max=%.2f n=%d" % (rule, r[rule]["mean_regret"], r[rule]["max_regret"],
                                                   r[rule]["n_runs"]))
    print("  n_runs=%d n_checkpoints=%d pooled_rM=%.3f pooled_entropy=%.3f" % (
        n_runs, n_ck, c["pooled_M"], c["pooled_entropy"]))
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
