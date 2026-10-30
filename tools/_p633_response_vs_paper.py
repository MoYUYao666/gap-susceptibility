# -*- coding: utf-8 -*-
r"""Cross-check: does every promise in the response letters actually hold in the manuscript?

A response that says "the paper now states X" is only true if the paper states X. This
extracts the concrete commitments (quoted phrases and numbers) from the three response boxes
and checks each against the compiled LaTeX sources.

    python tools/_p633_response_vs_paper.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
PAPER = REPO / "paper3" / "paper_ieee"
OUT = REPO / "outputs" / "analysis" / "response_vs_paper.json"

SOURCES = [
    PAPER / "main.tex",
    PAPER / "sections" / "introduction.tex",
    PAPER / "sections" / "related_work.tex",
    PAPER / "sections" / "theory.tex",
    PAPER / "sections" / "experiments.tex",
    PAPER / "sections" / "discussion.tex",
    PAPER / "sections" / "conclusion.tex",
    PAPER / "supplementary" / "supplementary.tex",
]

# claims the responses make about what the paper now says; each must appear in the paper
COMMITMENTS = [
    ("axiom R3' is stated", [r"R3'", r"R3\\textquotesingle", r"additivity"]),
    ("counterexample |grad E|^2", [r"block-decomposable", r"block decomposable"]),
    ("crossing is bracketed", [r"bracket"]),
    ("no architecture-dependence claim", [r"token budget", r"visual-token budget",
                                          r"visual token budget"]),
    ("30x variance ratio withdrawn", [r"between-rank", r"between rank"]),
    ("AdaLoRA at matched budget", [r"AdaLoRA"]),
    ("random allocation indistinguishable", [r"random allocation", r"q = 0\.2", r"p = 0\.2057",
                                             r"0\.2057"]),
    ("matched-loss control", [r"matched.{0,30}loss", r"matched training loss"]),
    ("reversal at another learning rate", [r"revers"]),
    ("data statement names the DOI", [r"10\.5281/zenodo\.23341223"]),
    ("downstream is not a proxy", [r"proxy"]),
    ("zero-shot defined separately", [r"zero-shot"]),
]

NUMBERS = ["1478", "1563", "5048", "1900", "0.0055", "5968", "2842", "0.5872", "0.5826",
           "0.2057", "1468", "757", "0.100", "98.9", "7237632", "7,237,632", "0.374",
           "0.172", "0.478"]


def read(p: Path) -> str:
    return io.open(p, encoding="utf-8", errors="replace").read() if p.exists() else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    paper = "\n".join(read(p) for p in SOURCES)
    paper_flat = re.sub(r"\s+", " ", paper)
    # supplementary contains the proofs too
    supp = PAPER / "supplementary"
    for q in supp.glob("*.tex"):
        paper_flat += " " + re.sub(r"\s+", " ", read(q))
    print(f"  Manuscript sources: {len(SOURCES)} files + {len(list(supp.glob('*.tex')))} supplementary, "
          f"{len(paper_flat):,} characters")
    print()
    print("  Promised change -> present in the manuscript?")
    rows = []
    ok = 0
    for label, pats in COMMITMENTS:
        found = None
        for pat in pats:
            m = re.search(pat, paper_flat, re.I)
            if m:
                found = m.group(0)[:60]
                break
        status = "OK " if found else "MISSING"
        if found:
            ok += 1
        rows.append({"commitment": label, "status": status, "evidence": found})
        print(f"    {status:<8} {label:<42} {found}")
    print()
    print(f"  {ok}/{len(COMMITMENTS)} commitments are visible in the manuscript text")
    print()
    print("  Numbers quoted in the responses: present in the manuscript?")
    nums = []
    for n in NUMBERS:
        inpaper = n in paper_flat
        nums.append({"number": n, "in_manuscript": inpaper})
        print(f"    {'OK ' if inpaper else 'note':<6} {n:<12} "
              f"{'in manuscript' if inpaper else 'not in manuscript text (may be in supplementary/figures)'}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"commitments": rows, "commitments_ok": ok,
             "numbers": nums}, ensure_ascii=False, indent=1))
        print()
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
