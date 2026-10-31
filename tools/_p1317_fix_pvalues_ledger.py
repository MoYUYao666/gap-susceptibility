# -*- coding: utf-8 -*-
r"""Fix the p-value formatting in the Williams paragraph and extend the A1 ledger with the new numbers.

The insertion script formatted p-values with one decimal, so 4.7e-06 rendered as "0.0". The paragraph is patched with
explicit scientific notation, and the ledger gains the Williams and selection numbers.

    python tools/_p1317_fix_pvalues_ledger.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
LEDGER = os.path.join(REPO, "tools", "_claim_ledger_a1.py")

FIXES = [
    ("($p=0.0$) in classification", r"($p=4.7\times10^{-6}$) in classification"),
    ("($p=0.0$) in retrieval", r"($p=2.6\times10^{-5}$) in retrieval"),
    ("($t=-5.5$, $p=0.0$)", r"($t=-5.5$, $p=7.2\times10^{-5}$)"),
]

LEDGER_ADD = '''    # ---- Williams tests and selection rule (strengthening round 3)
    wt = load("outputs/analysis/a1_williams_tests.json")
    claim("Williams CG vs M classification t", 7.2, wt["classification"]["williams"]["CG vs M(0.01)"]["t"],
          "...a1_williams_tests:classification.CG vs M(0.01).t", 1)
    claim("Williams CG vs M classification p", 4.7e-06, wt["classification"]["williams"]["CG vs M(0.01)"]["p"],
          "...:classification.CG vs M(0.01).p", 7)
    claim("Williams CG vs M retrieval t", 6.1, wt["retrieval"]["williams"]["CG vs M(0.01)"]["t"],
          "...:retrieval.CG vs M(0.01).t", 1)
    claim("Williams CG vs M retrieval p", 2.6e-05, wt["retrieval"]["williams"]["CG vs M(0.01)"]["p"],
          "...:retrieval.CG vs M(0.01).p", 7)
    claim("Williams CG vs tau classification p", 7.2e-05, wt["classification"]["williams"]["CG vs tau"]["p"],
          "...:classification.CG vs tau.p", 7)
    claim("Williams CG vs tau retrieval p", 0.75, wt["retrieval"]["williams"]["CG vs tau"]["p"],
          "...:retrieval.CG vs tau.p", 2)
    sel = load("outputs/analysis/a1_selection_rule.json")["selection"]
    claim("selection oracle top-1 (synthetic)", 78.1, sel["synthetic_configs"]["oracle_top1"],
          "...a1_selection_rule:synthetic_configs.oracle_top1", 1)
    claim("min-CG regret (synthetic)", 44.4, sel["synthetic_configs"]["rules"]["min_CG"]["regret"],
          "...:synthetic_configs.rules.min_CG.regret", 1)
    claim("min-M regret (synthetic)", 0.0, sel["synthetic_configs"]["rules"]["min_M(0.01)"]["regret"],
          "...:synthetic_configs.rules.min_M(0.01).regret", 1)
    tl = sel["templates"]
    claim("template regret min-M CLIP B/32", 1.7, tl["clip32"]["rules"]["min_mass_0.01"]["regret"],
          "...:templates.clip32.rules.min_mass_0.01.regret", 1)
    claim("template regret default CLIP B/32", 1.0, tl["clip32"]["rules"]["default_template"]["regret"],
          "...:templates.clip32.rules.default_template.regret", 1)
    claim("template rho CLIP B/32", -0.71, tl["clip32"]["spearman_mass_top1"], "...:templates.clip32.rho", 2)

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    for old, new in FIXES:
        n = t.count(old)
        print(f"  {old!r}: {n}")
        assert n == 1, old
        t = t.replace(old, new, 1)

    led = io.open(LEDGER, encoding="utf-8").read()
    if "Williams tests and selection rule" not in led:
        anchor = "    # ---- epoch sweep correlation (manuscript abstract/intro/epoch subsection)"
        assert led.count(anchor) == 1
        led = led.replace(anchor, LEDGER_ADD + anchor, 1)
        print("  ledger extended")
    else:
        print("  ledger already extended")

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(led)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
