# -*- coding: utf-8 -*-
r"""A1: insert the early-stopping baseline comparison into the monitoring paragraph.

Reads outputs/analysis/a1_stopping_baselines_rules.json and appends one sentence after the v2 monitoring paragraph.
Idempotent.

    python tools/_p1381_a1_baseline_insert.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

MAIN = "paper_a1/main.tex"
JSON = "outputs/analysis/a1_stopping_baselines_rules.json"
ANCHOR = "rather than of the statistic."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    r = d["rules"]
    n = d["correlation"]["n"]
    sentence = (r""" Adding a third held-out domain (fathomnet8, seven classes) and the standard confidence signals---six runs,
$%s$ checkpoints---does not change the ordering: the margin-mass rule costs $%.2f$ points of mean regret (worst $%.2f$),
against $%.2f$ for max-softmax, $%.2f$ for max-logit, $%.2f$ for predictive entropy and $%.2f$ for the log-sum-exp energy,
with the first epoch at $%.2f$ and the last at $%.2f$. The certificate is therefore not a re-parameterisation of a confidence
heuristic: the confidence signals do not rank these checkpoints the way accuracy does.""" % (
        n, r["min_M"]["mean_regret"], r["min_M"]["max_regret"], r["max_softmax"]["mean_regret"],
        r["max_logit"]["mean_regret"], r["min_entropy"]["mean_regret"], r["min_energy"]["mean_regret"],
        r["first"]["mean_regret"], r["last"]["mean_regret"]))
    t = io.open(MAIN, encoding="utf-8").read()
    if "Adding a third held-out domain (fathomnet8" in t:
        print("  already inserted")
        return 0
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + sentence, 1)
    print("  sentence:", sentence.strip()[:170], "...")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
