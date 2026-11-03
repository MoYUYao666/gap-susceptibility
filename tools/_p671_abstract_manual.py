# -*- coding: utf-8 -*-
r"""Write the abstract as paste-ready plain text, transliterating the mathematics by hand.

Five attempts at an automatic LaTeX-to-text converter each left damage: a greedy command
regex ate the leading letters of a word it had just produced (nabla -> abla, propto ->
"proportional to" gluing onto the next word). The abstract contains eight short formulas, so
an automatic converter buys nothing and risks a wrong symbol in a submitted form. The
mathematics is therefore transliterated here, once, and the file is written with assertions
that the text is plain and the formulas are intact.

    python tools/_p671_abstract_manual.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper3" / "paper_ieee" / "main.tex"
OUT = (REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD"
       / "P3_PRLETTERS-D-26-02378_Abstract.txt")

ABSTRACT = (
    "We allocate PEFT rank across the blocks of a multimodal model when the target cannot be "
    "searched, so the decision must come from the source model alone. The central object is "
    "the cross-modal gradient coupling Gamma_k = <grad_M_k E, u_M_k>. We ask what an "
    "admissible allocation statistic can be, and show that the five requirements we state "
    "formally force it to be additive in the per-block contributions - additivity being an "
    "assumption rather than a consequence, since block decomposability alone admits "
    "||grad E||^2. Given it, Gamma is unique up to positive scaling and the allocation is "
    "rank_k proportional to exp(-beta|Gamma_k|). Measured on CLIP, Gamma predicts a rank "
    "allocation for LLaVA instruction tuning with no target-model gradient. At identical "
    "trainable-parameter counts the allocation beats the uniform-rank baseline at one "
    "learning rate, but the advantage reverses at another and vanishes under matched training "
    "loss, so we report a zero-shot heuristic, not an optimum. Three controls bound its scope: "
    "it is indistinguishable from a random allocation of the same budget; AdaLoRA, swept over "
    "the same rates, reaches lower alignment energy than any of our arms; and the critical "
    "rank we had bracketed at r_c in [5, 6] belongs to the protocol, not to the model. That "
    "protocol is the largest caveat: its inputs are blank images, and at the paper's operating "
    "point a blank image carries three times the initialization alignment energy of a real "
    "one, so the objective optimised is not the one a real input induces."
)

KEYWORDS = ("PEFT Allocation, Representation Theorem, Phase Transition, "
            "Cross-Architecture Transfer, Multimodal Fine-tuning")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    words = len(ABSTRACT.split())
    problems = []
    if "\\" in ABSTRACT or "$" in ABSTRACT or "{" in ABSTRACT or "}" in ABSTRACT:
        problems.append("contains LaTeX characters")
    if re.search(r"(?<![a-zA-Z])abla", ABSTRACT):
        problems.append("severed nabla artefact")
    if "proportional toexp" in ABSTRACT or "rank_kproportional" in ABSTRACT:
        problems.append("glued maths")
    if words > 250:
        problems.append(f"{words} words exceeds the 250-word limit")
    # the formula count that had to be transliterated
    formulas = ["Gamma_k = <grad_M_k E, u_M_k>", "||grad E||^2",
                "exp(-beta|Gamma_k|)", "r_c in [5, 6]"]
    missing = [f for f in formulas if f not in ABSTRACT]
    if missing:
        problems.append(f"formula not found: {missing}")

    print(f"  words: {words} (limit 250)")
    print(f"  characters: {len(ABSTRACT)}")
    print(f"  formulas present: {len(formulas) - len(missing)}/{len(formulas)}")
    print(f"  problems: {problems if problems else 'none'}")

    print()
    print("=" * 100)
    print(ABSTRACT)
    print("=" * 100)
    print()
    print("KEYWORDS")
    print("=" * 100)
    print(KEYWORDS)
    print("=" * 100)

    if problems:
        print("  refusing to write")
        return 1
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            ABSTRACT + "\n\nKEYWORDS: " + KEYWORDS + "\n")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
