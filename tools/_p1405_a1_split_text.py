# -*- coding: utf-8 -*-
r"""A1: rewrite the monitoring wording with the split-size diagnosis.

Replaces the two sentences added earlier with the stratified, sampling-noise-aware statement, and updates the ledger.

    python tools/_p1405_a1_split_text.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import json

MAIN = "paper_a1/main.tex"
LEDGER = "tools/_claim_ledger_a1.py"
JSON = "outputs/analysis/a1_monitor_split_diagnosis.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    s, l = d["summary"]["small"], d["summary"]["large"]
    intro = ("\n\nOn the monitoring side, the margin mass selects epochs close to the labelled oracle when the held-out split\n"
             "is large enough: across %d runs with held-out splits of %d--%d images the minimum-mass rule lands $%.2f$\n"
             "points from the oracle on average ($%.2f$ binomial standard errors), against $%.2f$ for the first epoch;\n"
             "training to the end reaches $%.2f$, so the rule buys early stopping without an accuracy cost but does not\n"
             "improve on it. On the four small splits (%d--%d images) every rule is dominated by sampling noise: minimum\n"
             "mass $%.2f$ points ($%.2f$ SE), last epoch $%.2f$, first epoch $%.2f$." % (
                 l["n_runs"], l["n_eval_range"][0], l["n_eval_range"][1], l["mean_regret_minM"],
                 l["mean_regret_minM_in_SE"], l["mean_regret_first_epoch"], l["mean_regret_last_epoch"],
                 s["n_eval_range"][0], s["n_eval_range"][1], s["mean_regret_minM"], s["mean_regret_minM_in_SE"],
                 s["mean_regret_last_epoch"], s["mean_regret_first_epoch"]))
    para = (" Stratifying by held-out size explains the expanded-set reversal: on the %d runs whose holdout has %d--%d\n"
            "images the minimum-mass rule costs $%.2f$ points (against $%.2f$ for training to the end and $%.2f$ for the\n"
            "first epoch), while on the %d small holdouts (%d--%d images) every rule is within sampling noise---minimum\n"
            "mass $%.2f$ points ($%.2f$ binomial SE), last epoch $%.2f$, first epoch $%.2f. The certificate is therefore a\n"
            "selection statistic for evaluations large enough to resolve it, not a universal stopping rule, and it buys\n"
            "early stopping rather than an accuracy gain." % (
                l["n_runs"], l["n_eval_range"][0], l["n_eval_range"][1], l["mean_regret_minM"],
                l["mean_regret_last_epoch"], l["mean_regret_first_epoch"], s["n_runs"], s["n_eval_range"][0],
                s["n_eval_range"][1], s["mean_regret_minM"], s["mean_regret_minM_in_SE"], s["mean_regret_last_epoch"],
                s["mean_regret_first_epoch"]))
    t = io.open(MAIN, encoding="utf-8").read()
    start = t.find("\n\nOn the monitoring side")
    end = t.find("\n\nThe paper also turns", start)
    if start >= 0 and end > start:
        t = t[:start] + intro + t[end:]
        print("  intro sentence replaced")
    else:
        print("  intro anchor not found; skipped")
    k = t.find(" Extending this comparison with two further seeds")
    if k >= 0:
        m = t.find("stopping rule.", k)
        t = t[:k] + para + t[m + len("stopping rule."):]
        print("  paragraph sentence replaced")
    else:
        print("  paragraph anchor not found; skipped")

    block = '''    # ---- split-size stratified monitoring diagnosis
    split = load("outputs/analysis/a1_monitor_split_diagnosis.json")
    _s, _l = split["summary"]["small"], split["summary"]["large"]
    claim("large-split runs", %d, _l["n_runs"], "...a1_monitor_split_diagnosis", 0)
    claim("large-split min-M mean regret", %.2f, _l["mean_regret_minM"], "...a1_monitor_split_diagnosis", 2)
    claim("large-split last-epoch mean regret", %.2f, _l["mean_regret_last_epoch"], "...a1_monitor_split_diagnosis", 2)
    claim("large-split first-epoch mean regret", %.2f, _l["mean_regret_first_epoch"], "...a1_monitor_split_diagnosis", 2)
    claim("small-split runs", %d, _s["n_runs"], "...a1_monitor_split_diagnosis", 0)
    claim("small-split min-M mean regret", %.2f, _s["mean_regret_minM"], "...a1_monitor_split_diagnosis", 2)
    claim("small-split last-epoch mean regret", %.2f, _s["mean_regret_last_epoch"], "...a1_monitor_split_diagnosis", 2)
    claim("small-split min-M regret in SE", %.2f, _s["mean_regret_minM_in_SE"], "...a1_monitor_split_diagnosis", 2)

''' % (l["n_runs"], l["mean_regret_minM"], l["mean_regret_last_epoch"], l["mean_regret_first_epoch"],
       s["n_runs"], s["mean_regret_minM"], s["mean_regret_last_epoch"], s["mean_regret_minM_in_SE"])
    led = io.open(LEDGER, encoding="utf-8").read()
    if "split-size stratified monitoring diagnosis" not in led:
        anchor = "    # ---- epoch sweep correlation (manuscript abstract/intro/epoch subsection)"
        assert led.count(anchor) == 1
        led = led.replace(anchor, block + anchor, 1)
        print("  ledger block added")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(led)
    ast.parse(led)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
