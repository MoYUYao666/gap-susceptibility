# -*- coding: utf-8 -*-
r"""Remove the sentence in Corollary 3's prose that the new corollary statement now says.

Wrapping the corollary subsections in `corollary` environments put each statement in the environment and
left the original prose sentence below it, so Corollary 3 reads the crossing condition twice in a row.
The prose keeps everything the statement does not carry.

    python tools/_p909_p3_dedupe_corollary3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
THEORY = REPO / "paper3" / "paper_ieee" / "sections" / "theory.tex"

OLD = ("Corollaries~\\ref{cor:gradient-flow} and~\\ref{cor:optimal} jointly imply a "
       "\\textbf{critical rank threshold} $r_c$ at which the sign\n"
       "of $\\Delta E$ flips: $\\mathrm{sgn}(\\Delta E)=-1$ for $r<r_c$ and $+1$ for $r>r_c$. Below\n")
NEW = "Below\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = THEORY.read_text(encoding="utf-8")
    if OLD not in t:
        print("  the duplicated sentence is not present (already removed or reworded)")
        return 0
    assert t.count(OLD) == 1, f"found {t.count(OLD)} occurrences"
    if not a.apply:
        print("  (dry run) would drop the duplicated sentence and keep the rest of the paragraph")
        return 0
    THEORY.write_text(t.replace(OLD, NEW, 1), encoding="utf-8", newline="")
    check = THEORY.read_text(encoding="utf-8")
    assert "jointly imply a" not in check.split("\\end{corollary}")[1].split("\\subsection")[0], \
        "the duplicated sentence is still in the prose"
    assert "Below\n$r_c$ LoRA capacity cannot develop" in check, "the paragraph tail changed unexpectedly"
    print("  removed; the paragraph now opens with \"Below $r_c$ LoRA capacity cannot ...\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
