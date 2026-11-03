# -*- coding: utf-8 -*-
r"""A1: add the retrieval, training-mass and epochs-saved results to the monitoring section.

    python tools/_p1439_a1_insert_round1.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
ANCHOR = ("selection statistic for evaluations large enough to resolve it, not a universal stopping rule, and it buys\n"
          "early stopping rather than an accuracy gain.")
TEXT = ("""

Two further checks use the same rule. On an in-batch retrieval task---137 held-out marine image-caption pairs,
400 training pairs, the text tower adapted---accuracy peaks at the sixth epoch (R@1 $22.8\\%$) and the minimum-mass
epoch (the eighth) reaches $22.1\\%$, a regret of $0.7$ points against $2.9$ for training to the end
(\\texttt{outputs/\\allowbreak analysis/\\allowbreak a1\\_retrieval\\_monitor.json}). Replacing the held-out mass with the
training-split mass, which is larger and always labelled, does not repair the small-holdout failure: across the four
small-split runs it costs $1.43$ points against $1.04$ for the held-out mass and $1.65$ for the last epoch, so the
limiting factor is the size of the evaluation split rather than the availability of labels
(\\texttt{outputs/\\allowbreak analysis/\\allowbreak a1\\_monitor\\_trainmass.json}). What the rule buys is compute: on the
16 large-split runs it stops $2.6$ epochs early on average at a cost of $0.06$ points relative to training to the end
(\\texttt{outputs/\\allowbreak analysis/\\allowbreak a1\\_monitor\\_diagnosis.json}).""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    assert "Two further checks use the same rule" not in t
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + TEXT, 1)
    print("  paragraph inserted")
    if a.apply:
        io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
