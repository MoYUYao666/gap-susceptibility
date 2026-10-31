# -*- coding: utf-8 -*-
r"""Before touching anything, check how the manuscript and supplementary express four values.

The four are: the matched parameter budget, the 3e-4 learning rate, corner-vs-uniform
p = 0.0587, and the Qwen token count 50176. Each may already be in the paper in another
notation (3 x 10^-4, 0.06, ~50k tokens, a budget in millions). This prints the surrounding
text so the decision is made on evidence.

    python tools/_p637_inspect_four.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper3" / "paper_ieee"
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"

PROBES = [
    ("parameter budget", [r"budget", r"trainable parameter", r"parameters", r"param"],
     [r"7,?237", r"7\.2", r"7\s*million"]),
    ("learning rate 3e-4", [r"3\s*\\times\s*10\^\{?-?4", r"3e-?4", r"0\.0003",
                            r"learning rate", r"\\eta"],
     [r"10\^\{-4\}", r"\\times10"]),
    ("corner vs uniform", [r"corner", r"0\.0587", r"0\.059", r"0\.06\b", r"0\.055"],
     [r"corner"]),
    ("Qwen token count", [r"50,?176", r"token budget", r"tokens", r"visual token",
                          r"blank"],
     [r"50,?176", r"49,?152"]),
]


def read(p: Path) -> str:
    try:
        return io.open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = [PAPER / "main.tex"] + sorted((PAPER / "sections").glob("*.tex")) + \
            sorted((PAPER / "supplementary").glob("*.tex"))
    corpus = {str(p.relative_to(REPO)): read(p) for p in files}
    # also the compiled supplementary PDF, since tables may live only there
    supp_pdf = PAPER / "supplementary" / "supplementary.pdf"
    if supp_pdf.exists():
        r = subprocess.run(["pdftotext", "-q", "-layout", str(supp_pdf), "-"],
                           capture_output=True)
        corpus["[pdf] supplementary.pdf"] = r.stdout.decode("utf-8", errors="replace")
    main_pdf = PAPER / "main.pdf"
    if main_pdf.exists():
        r = subprocess.run(["pdftotext", "-q", "-layout", str(main_pdf), "-"],
                           capture_output=True)
        corpus["[pdf] main.pdf"] = r.stdout.decode("utf-8", errors="replace")

    for label, pats, extra in PROBES:
        print("=" * 96)
        print(f"{label}")
        print("=" * 96)
        for pat in pats:
            hits = []
            for name, t in corpus.items():
                for m in re.finditer(pat, t, re.I):
                    ln = t[:m.start()].count("\n") + 1
                    seg = " ".join(t[max(0, m.start() - 150):m.start() + 150].split())
                    hits.append((name, ln, seg))
            if hits:
                print(f"  pattern /{pat}/  ({len(hits)} hits) — first 3:")
                for name, ln, seg in hits[:3]:
                    print(f"    {name}:{ln}")
                    print(f"       {seg[:230]}")
                print()
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
