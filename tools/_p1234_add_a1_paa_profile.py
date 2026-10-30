# -*- coding: utf-8 -*-
r"""Add an `a1_paa` audit profile (Pattern Analysis and Applications) next to `a1_nn`.

A1's venue moved from Neural Networks (desk-rejected) to Pattern Analysis and Applications, whose requirements differ:
abstract 150-250 words, 4-6 keywords, a single Declarations section with Springer's sub-items, and a separate title page.
Auditing A1 against the n:n profile therefore reports C-09 failures that no longer apply.

    python tools/_p1234_add_a1_paa_profile.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES = os.path.join(REPO, "tools", "paper_audit", "profiles.py")

ANCHOR = '    "a23_joe": _p('

BLOCK = '''    "a1_paa": _p(
        "a1_paa", "A1 - Pattern Analysis and Applications (Springer)",
        manuscript="paper_a1",
        tex=["main.tex", "title_page.tex"],
        pdfs=["main.pdf", "title_page.pdf"],
        logs=["main.log", "title_page.log"],
        limits={"abstract_words_min": 150, "abstract_words_max": 250,
                "keywords_min": 4, "keywords_max": 6},
        required_sections=["Introduction", "Setup", "Results", "Discussion", "Conclusion"],
        required_declarations=["Funding", "Competing interests", "Ethics approval",
                               "Consent for publication", "Data and code availability",
                               "Authors' contributions", "Use of artificial-intelligence tools"],
        forbidden_strings=["under review at Pattern Recognition", "Manuscript under review."],
        commands=[],
        build_command=["pdflatex", "-interaction=nonstopmode", "main.tex"],
        freeze_paths=["SUBMISSION/A1_NeuralNetworks"],
        notes=("Prepared for Pattern Analysis and Applications (SCIE); not yet submitted. "
               "The Neural Networks package under SUBMISSION/ must stay frozen."),
    ),

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(PROFILES, encoding="utf-8").read()
    if '"a1_paa"' in t:
        print("  profile already present")
        return 0
    n = t.count(ANCHOR)
    print(f"  anchor {ANCHOR!r}: {n}")
    assert n == 1
    t = t.replace(ANCHOR, BLOCK + ANCHOR, 1)
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(PROFILES, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
