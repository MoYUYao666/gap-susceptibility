# -*- coding: utf-8 -*-
"""Verify that the R1 revision content survives in the resubmission PDFs.

    python tools/_p1497_r1_carryover_check.py
"""
from __future__ import annotations

import io
import re
import os

from pypdf import PdfReader

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(REPO, "SUBMISSION", "P3_PRL_resubmission")


def text(path):
    t = "".join((p.extract_text() or "") for p in PdfReader(path).pages)
    t = re.sub(r"-\s*\n\s*", "", t)
    return " ".join(t.split()).lower()


def main() -> int:
    m = text(os.path.join(PKG, "Manuscript.pdf"))
    s = text(os.path.join(PKG, "Supplementary.pdf"))
    both = m + " " + s
    checks = {
        "R1.5 axiom R3'": "r3" in both and "additiv" in both,
        "R2.2 block-wise allocation": "block-wise" in both or "blockwise" in both,
        "R1.3/R3.16 downstream retrieval": "r@1" in both or "retrieval" in both,
        "R2.4/R3.9 adalora": "adalora" in both,
        "R3.9 halora/IGU": "halora" in both or "igu" in both or "shap" in both or "ntk" in both,
        "R1.4 real pairs": "real image" in both,
        "R3.13 blank image ratio": "3.09" in both or "three times" in both,
        "R3.17/R3.19 bracketed crossing": "bracket" in both,
        "R3.20 variance ratio withdrawn": "30" in both and ("variance" in both or "eta" in both),
        "R3.12 per-block gamma table": "per-block" in both,
        "R3.18 reproducibility": "reproduc" in both,
        "R3.7 beta selection": "beta" in both or "β" in both,
        "R3.5 hessian": "hessian" in both,
        "R3.6 first-order scope": "first-order" in both or "first order" in both,
        "R3.22 nan diagnostics": "nan" in both,
        "R3.23 other dataset": "flickr" in both or "caption" in both,
        "R3.4 monte-carlo": "monte" in both or "reference batch" in both,
        "R2.1 zero-shot definition": "zero-shot" in both,
        "R1.4 newer family": "qwen" in both,
        "5-seed p=0.008 (new)": "0.008" in both,
        "protocol shift S16 (new)": "protocol" in both,
        "claim status S17 (new)": "claim status" in both or "claim-status" in both,
    }
    for k, v in checks.items():
        print(f"  {k:42s} {v}")
    missing = [k for k, v in checks.items() if not v]
    print("  missing:", missing if missing else "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
