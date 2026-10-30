# -*- coding: utf-8 -*-
r"""A1: supersede the v1 interior-optimum paragraph with the extended v2 validation (2 backbones, 3 seeds, sequential rules).

    python tools/_p1363_a1_monitor_v2_insert.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io

MAIN = "paper_a1/main.tex"
LEDGER = "tools/_claim_ledger_a1.py"

OLD_START = "The transfer setting has no interior optimum"
OLD_END = "rather than of the statistic."

NEW = r"""The transfer setting has no interior optimum, but a same-domain evaluation does, and there the stopping rule can be
tested properly. We fine-tuned LoRA on the text tower of two frozen backbones (ViT-B/32 and ViT-L/14) on DTD (47 classes)
and Food-101 (101 classes), holding out a per-class split, and scored the held-out split after every epoch for ten epochs
(three seeds each, twelve runs: \texttt{outputs/\allowbreak analysis/\allowbreak a1\_monitor\_interior\_v2.json}). Accuracy
is non-monotone: the best epoch ranges from the second to the tenth across runs (median sixth), and the first epoch is far
from optimal (mean regret $3.54$ points). Selecting the epoch by the smallest $M(0.01)$ over the trajectory reaches mean
regret $0.41$ points (worst $1.28$); the same rule that uses only the epochs seen so far---stop when $M(0.01)$ rises more
than $0.01$ above its running minimum---reaches $0.50$ (worst $1.56$), which is competitive with training to the end
($0.60$) and clearly better than the first epoch ($3.54$), while the gap version of the same rule costs $1.68$ and its
oracle $1.53$. Across the $120$ checkpoints the mass tracks accuracy at $r=-0.986$; the gap's pooled correlation is
$+0.78$, yet every gap-based stopping rule is worse than every mass-based one. The certificate is therefore usable as an
early-stopping signal in the regime where early stopping is a real decision; its failure to beat the trivial first-epoch
rule in the transfer regime is a property of that regime's monotone trajectories rather than of the statistic."""

LEDGER_BLOCK = '''    # ---- interior-optimum monitoring validation (v2: 2 backbones x 2 datasets x 3 seeds x 10 epochs)
    mon = load("outputs/analysis/a1_monitor_interior_v2.json")
    rules = load("outputs/analysis/a1_monitor_interior_v2_rules.json")
    _n = rules["correlation"]["n_checkpoints"]
    claim("interior v2 checkpoints", 120, _n, "...a1_monitor_interior_v2_rules", 0)
    claim("interior v2 r(M,top1)", -0.986, rules["correlation"]["pooled_M"], "...a1_monitor_interior_v2_rules", 3)
    claim("interior v2 r(CG,top1)", 0.781, rules["correlation"]["pooled_CG"], "...a1_monitor_interior_v2_rules", 3)
    claim("interior v2 min-M mean regret", 0.41, rules["rules"]["minM"]["mean_regret"], "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 seq-M 0.01 mean regret", 0.50, rules["rules"]["seqM0.01"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 min-CG mean regret", 1.53, rules["rules"]["minCG"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 last-epoch mean regret", 0.60, rules["rules"]["last"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 first-epoch mean regret", 3.54, rules["rules"]["first"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 gap rule mean regret", 1.68, rules["rules"]["seqCG0.01"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    i = t.find(OLD_START)
    j = t.find(OLD_END, i)
    assert i > 0 and j > i, (i, j)
    j += len(OLD_END)
    t = t[:i] + NEW + t[j:]
    print("A1 paragraph replaced")
    l = io.open(LEDGER, encoding="utf-8").read()
    start = l.find("    # ---- interior-optimum monitoring validation")
    end = l.find("    # ---- epoch sweep correlation")
    assert start > 0 and end > start, (start, end)
    l = l[:start] + LEDGER_BLOCK + l[end:]
    ast.parse(l)
    print("ledger block replaced")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(l)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
