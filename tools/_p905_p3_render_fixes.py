# -*- coding: utf-8 -*-
r"""Fix the three rendering faults in P3's main text:

1. **No space before the theorem note.** IEEEtran's theorem style prints "Theorem III.1(Representation
   Theorem)." -- the `\newtheoremstyle` used has an empty after-head punctuation, so the note runs into
   the number. Two styles are defined here (plain for theorem/lemma/corollary, definition for
   definition/remark) with the standard 5pt space and the end-of-proof square only where a proof ends.
2. **A duplicated label.** `sections/theory.tex` puts `\label{lem:r3-not-r3p}` on both the Gap
   Susceptibility definition and the "R3 does not imply R3'" lemma, so the label is multiply defined and
   `\ref` can resolve to either. The definition gets its own label.
3. **Visible link borders.** hyperref defaults to drawing a green rectangle around every citation and
   cross-reference, and no `hypersetup` is given, so the submitted PDF is full of them. `hidelinks`
   keeps the links and drops the boxes.

Applied to all three main-text variants (`main.tex`, `main_full.tex`, `main_10pp.tex`) so they cannot
disagree, and asserted afterwards.

    python tools/_p905_p3_render_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
THEORY = P3 / "sections" / "theory.tex"
VARIANTS = [P3 / "main.tex", P3 / "main_full.tex", P3 / "main_10pp.tex"]

NUMERATION = ("\\newtheorem{theorem}{Theorem}[section]\n"
              "\\newtheorem{corollary}{Corollary}[theorem]\n"
              "\\newtheorem{lemma}{Lemma}[theorem]\n"
              "\\newtheorem{definition}{Definition}[section]\n"
              "\\theoremstyle{definition}\n"
              "\\newtheorem{remark}{Remark}[section]")

STYLES = r"""% Theorem-like styles (2026-10-15).
% IEEEtran's own style leaves an empty punctuation after the head, which printed
% "Theorem III.1(Representation Theorem)." with no space; these two styles restore the standard
% 5pt separation and keep the body upright, as IEEE papers set theorem statements.
\newtheoremstyle{p3plain}%
  {5pt}% space above
  {5pt}% space below
  {\normalfont}% body font
  {}% indent
  {\bfseries}% head font
  {.}% punctuation after the head
  {5pt}% space after the head
  {}% head spec (empty = "Theorem III.1.")
\newtheoremstyle{p3defn}%
  {5pt}% space above
  {5pt}% space below
  {\normalfont}% body font
  {}% indent
  {\bfseries}% head font
  {.}% punctuation after the head
  {5pt}% space after the head
  {}% head spec

\theoremstyle{p3plain}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{corollary}{Corollary}[theorem]
\newtheorem{lemma}{Lemma}[theorem]
\theoremstyle{p3defn}
\newtheorem{definition}{Definition}[section]
\newtheorem{remark}{Remark}[section]"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for p in VARIANTS:
        t = p.read_text(encoding="utf-8")
        if "newtheoremstyle{p3plain}" in t:
            print(f"  {p.name}: already patched")
            continue
        assert t.count(NUMERATION) == 1, f"{p.name}: theorem declarations not found as expected"
        t = t.replace(NUMERATION, STYLES, 1)
        # hide the link borders once, right after hyperref is loaded
        assert "hidelinks" not in t
        t = t.replace("\\usepackage{hyperref}",
                      "\\usepackage{hyperref}\n"
                      "\\hypersetup{hidelinks}   % no coloured link boxes in the print version", 1)
        if a.apply:
            p.write_text(t, encoding="utf-8", newline="")
        print(f"  {p.name}: styles inserted, hidelinks set")

    th = THEORY.read_text(encoding="utf-8")
    if "def:gap-susceptibility" in th:
        print("  theory.tex: label already unique")
    else:
        old = ("\\begin{definition}[Gap Susceptibility]\n"
               "$\\Gamma_k := \\langle \\nabla_{M_k}E, \\mathbb{E}_{\\mathrm{batch}}"
               "[\\nabla_{M_k}L]\\rangle$.\n"
               "\\end{definition}")
        new = ("\\begin{definition}[Gap Susceptibility]\\label{def:gap-susceptibility}\n"
               "$\\Gamma_k := \\langle \\nabla_{M_k}E, \\mathbb{E}_{\\mathrm{batch}}"
               "[\\nabla_{M_k}L]\\rangle$.\n"
               "\\end{definition}")
        assert th.count(old) == 1, "the definition block was not found exactly once"
        th = th.replace(old, new, 1)
        if a.apply:
            THEORY.write_text(th, encoding="utf-8", newline="")
        print("  theory.tex: the definition got its own label")

    if not a.apply:
        print("  (dry run)")
        return 0

    for p in VARIANTS:
        t = p.read_text(encoding="utf-8")
        assert "newtheoremstyle{p3plain}" in t and "hidelinks" in t
    th2 = THEORY.read_text(encoding="utf-8")
    # the string also appears in a \ref, so count the label declaration, not the bare name
    assert th2.count("\\label{lem:r3-not-r3p}") == 1, "the duplicate label is still there"
    assert th2.count("\\ref{lem:r3-not-r3p}") >= 1, "the lemma is no longer referenced"
    assert "def:gap-susceptibility" in th2
    print("  verified: styles in all variants, labels unique")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
