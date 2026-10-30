# -*- coding: utf-8 -*-
r"""Paper A upgrade: add the protocol-dependence result (effective batch changes alpha and beta).

    python tools/_p1477_paperA_protocol.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMP = os.path.join(REPO, "paper合", "sections", "empirical.tex")
MAINS = [os.path.join(REPO, "paper合", "main_nc.tex"), os.path.join(REPO, "paper合", "main_springer.tex")]

ANCHOR = "through the qualitative position ordering."
PARA = ("\n\n\\textbf{Protocol dependence.} Holding the model, task data, seed, site and family fixed and changing only the\n"
        "gradient accumulation (effective batch $32\\to128$), the fitted $\\alpha$ nearly doubles ($-0.0345\\to-0.0669$) and\n"
        "$\\beta$ falls by $35\\%$ ($0.1091\\to0.0713$), with both fits above $R^2=0.89$\n"
        "(\\texttt{outputs/\\allowbreak analysis/\\allowbreak ode\\_ledger.json}, the \\texttt{verify\\_accum} entries).\n"
        "$\\alpha$ and $\\beta$ are therefore protocol functionals rather than model constants: this is why every ODE\n"
        "comparison in this paper is made at a matched protocol, and why the coefficients are never pooled across\n"
        "configurations.")
ABS_OLD = "we report an association, not a predictor."
ABS_NEW = ("we report an association, not a predictor, and show that its coefficients are protocol functionals, not model "
           "constants.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    e = io.open(EMP, encoding="utf-8").read()
    if "Protocol dependence." not in e:
        assert e.count(ANCHOR) == 1, e.count(ANCHOR)
        e = e.replace(ANCHOR, ANCHOR + PARA, 1)
        io.open(EMP, "w", encoding="utf-8", newline="").write(e)
        print("  protocol paragraph inserted")
    for m in MAINS:
        t = io.open(m, encoding="utf-8").read()
        if ABS_OLD in t and ABS_NEW not in t:
            io.open(m, "w", encoding="utf-8", newline="").write(t.replace(ABS_OLD, ABS_NEW, 1))
            print("  abstract clause added to", os.path.basename(m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
