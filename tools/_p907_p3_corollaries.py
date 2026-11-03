# -*- coding: utf-8 -*-
r"""Turn P3's five "Corollary N" subsections into real corollary environments, with labels.

Why the numbering is the way it is: the source already calls these Corollary 1..5, the supplement cites
"Corollary 5" by hand, and the capacity-matched comparison is described against "Corollary 4". So the
new environments keep a counter of their own (`\newtheorem{corollary}{Corollary}`, no section prefix),
which prints Corollary 1..5 exactly as before, instead of deriving from the theorem counter. Deriving
from it would have renumbered them to III.D/E/F and forced edits in the supplement and appendix.

Also listed here, and fixed, are the hard-coded "Corollary~4" / "Corollary~5" strings in the prose: they
become \ref to the new labels, so they follow the counters. `relations()` prints the resulting map so the
supplement's hand-written numbers can be checked against it.

    python tools/_p907_p3_corollaries.py [--apply]
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

OLD_DECL = ("\\theoremstyle{p3plain}\n"
            "\\newtheorem{theorem}{Theorem}[section]\n"
            "\\newtheorem{corollary}{Corollary}[theorem]\n"
            "\\newtheorem{lemma}{Lemma}[theorem]\n")

NEW_DECL = ("\\theoremstyle{p3plain}\n"
            "\\newtheorem{theorem}{Theorem}[section]\n"
            "\\newtheorem{lemma}{Lemma}[section]\n"
            "% The corollaries keep a counter of their own. The source already numbers them 1..5 and the\n"
            "% supplement cites \"Corollary 5\" by hand, so a section- or theorem-derived number would\n"
            "% renumber them and break that cross-document reference.\n"
            "\\newtheorem{corollary}{Corollary}\n")

# (subsection title in the source, new corollary label, corollary title, statement)
COROLLARIES = [
    ("Corollary 1: First-Order Gradient Flow", "cor:gradient-flow", "First-Order Gradient Flow",
     "For $\\Delta\\theta_k=-\\eta u_k$, the alignment-energy change decomposes as\n"
     "$\\Delta E_k = -\\eta\\Gamma_k + \\tfrac{1}{2}\\eta^2 H_k + D_k$, with "
     "$H_k=\\langle u_k,\\nabla^2_{M_k}E\\,u_k\\rangle$ the curvature and "
     "$\\mathbb{E}[D_k]=0$."),
    ("Corollary 2: Optimal Allocation", "cor:optimal", "Optimal Allocation",
     "Under (A1)--(A4) below, the rank allocation that minimizes expected alignment degradation is\n"
     "$\\mathrm{rank}^*_k \\propto \\exp(-\\beta|\\Gamma_k|)$, with $\\beta$ a temperature that is not "
     "fitted on the target architecture."),
    ("Corollary 3: Alignment Phase Transition", "cor:phase-transition", "Alignment Phase Transition",
     "Corollaries~\\ref{cor:gradient-flow} and~\\ref{cor:optimal} jointly imply a critical rank $r_c$ at "
     "which the sign of $\\Delta E$ flips: $\\mathrm{sgn}(\\Delta E)=-1$ for $r<r_c$ and $+1$ for $r>r_c$."),
    ("Corollary 4: Cross-Architecture Transfer", "cor:transfer", "Cross-Architecture Transfer",
     "The relative ordering of $|\\Gamma_k|$ is invariant under the orthogonal subgroup, and the "
     "allocation depends only on that ordering, so a \\emph{Partial Ordering Preservation} carries the "
     "allocation across architectures up to a monotonic distortion."),
    ("Corollary 5: Paper~2 as Retrieval Specialization", "cor:retrieval-specialization",
     "Paper~2 as Retrieval Specialization",
     "Setting $K=\\{\\text{vision},\\text{text}\\}$, $E=DG^*$ and $u=\\nabla L_{\\mathrm{InfoNCE}}$ "
     "recovers $d(DG^*)/dt=\\alpha-\\beta(DG^*-DG_0)$ as a natural special case."),
]

# prose references that were written as numbers; the files are patched once, at the end, so a later
# write cannot undo an earlier one (an earlier version of this script did exactly that: it wrote the
# prose replacements and then overwrote them with the pre-change copy of theory.tex)
PROSE = [
    (THEORY, "Corollary~4", "\\ref{cor:transfer}"),
    (P3 / "sections" / "discussion.tex", "Corollary~4", "\\ref{cor:transfer}"),
    (P3 / "sections" / "experiments.tex", "Corollary~4", "\\ref{cor:transfer}"),
    (P3 / "sections" / "appendix.tex", "Corollary~5", "\\ref{cor:retrieval-specialization}"),
    # The supplement is compiled as its own document, so a \ref into the main text cannot resolve.
    # Its pointers stay as plain text, kept in step by hand.
    (P3 / "supplementary" / "supplementary.tex", "Corollary~5",
     "Corollary~5 of the main text"),
    (P3 / "supplementary" / "supplementary.tex", "Lemma~1 of the main text",
     "Lemma~2 of the main text"),
    (P3 / "supplementary" / "supplementary.tex", "Theorem 1", "Theorem~1"),
]
THEORY_EXTRA = [("Corollaries~1 and 2", "Corollaries~\\ref{cor:gradient-flow} and~\\ref{cor:optimal}")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for p in VARIANTS:
        t = p.read_text(encoding="utf-8")
        # Check the exact declaration, not a substring: `\newtheorem{corollary}{Corollary}[theorem]`
        # also starts with the string used for the new form, which is how an earlier run skipped this.
        if "\\newtheorem{corollary}{Corollary}\n" in t and "\\newtheorem{lemma}{Lemma}[section]" in t:
            print(f"  {p.name}: counters already set")
            continue
        assert t.count(OLD_DECL) == 1, f"{p.name}: theorem declarations not found as expected"
        if a.apply:
            p.write_text(t.replace(OLD_DECL, NEW_DECL, 1), encoding="utf-8", newline="")
        print(f"  {p.name}: corollary counter decoupled, lemma numbered by section")

    th = THEORY.read_text(encoding="utf-8")
    for old_head, label, title, stmt in COROLLARIES:
        if f"\\label{{{label}}}" in th:
            print(f"  {label}: already present")
            continue
        old = "\\subsection{" + old_head + "}\n"
        assert th.count(old) == 1, f"subsection heading not found exactly once: {old_head!r}"
        new = ("\\subsection{" + title + "}\n\n"
               "\\begin{corollary}[" + title + "]\\label{" + label + "}\n" + stmt + "\n"
               "\\end{corollary}\n")
        th = th.replace(old, new, 1)
        print(f"  {label}: subsection became a corollary")
    for old, new in THEORY_EXTRA:
        if old in th:
            th = th.replace(old, new)
            print(f"  theory.tex: {old} -> {new}")
    for path, old, new in PROSE:
        if path == THEORY:
            continue                      # handled through `th` above, written once below
        t = path.read_text(encoding="utf-8")
        c = t.count(old)
        if c:
            if a.apply:
                path.write_text(t.replace(old, new), encoding="utf-8", newline="")
            print(f"  {path.name}: {old} -> {new}  ({c} occurrence(s))")
    # the prose references inside theory.tex go through the same single write as the environments
    for path, old, new in PROSE:
        if path != THEORY:
            continue
        c = th.count(old)
        if c:
            th = th.replace(old, new)
            print(f"  theory.tex: {old} -> {new}  ({c} occurrence(s))")
    if a.apply:
        THEORY.write_text(th, encoding="utf-8", newline="")

    # what number each corollary will print
    print()
    print("  resulting labels (corollary counter, document order):")
    for i, (_h, label, title, _s) in enumerate(COROLLARIES, 1):
        print(f"    Corollary {i}: {title}   [{label}]")
    print("  theorem/lemma counters after the change:")
    print("    Theorem III.1 (Representation Theorem)   -> unchanged")
    print("    Lemma III.2 (R3 does not imply R3')      -> was Lemma III.1.1")
    print("    Theorem III.3 (Projection Error Bound)   -> was Theorem III.2")

    if not a.apply:
        print("  (dry run)")
        return 0

    th2 = THEORY.read_text(encoding="utf-8")
    assert th2.count("\\begin{corollary}") == 5, th2.count("\\begin{corollary}")
    assert "Corollary 1:" not in th2 and "Corollary 5:" not in th2
    assert "Corollary~4" not in th2
    for p in VARIANTS:
        assert "\\newtheorem{corollary}{Corollary}" in p.read_text(encoding="utf-8")
    print("  verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
