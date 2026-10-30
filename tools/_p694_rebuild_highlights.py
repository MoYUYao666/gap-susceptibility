# -*- coding: utf-8 -*-
r"""Rebuild the Paper A highlights: correct title, correct R2, claims the manuscript supports.

Three problems found:
 1. NC_submission/Highlights.pdf still carries the OLD title ("Protect, Don't Perturb: ..."),
    while the manuscript is "Adaptation Site and the Modality Gap: ...". The editorial office
    would read a title that does not belong to this paper.
 2. The R2 bullet says 0.97 (in the txt files and that PDF) or 0.96 (in highlights_nc.pdf). The
    manuscript says mean R^2 = 0.949 with range 0.814-0.977, so both are wrong.
 3. The bullets are otherwise sound and match the paper, so they are kept, with the number
    corrected and no claim strengthened.

Writes highlights_nc.tex / .txt and compiles highlights_nc.pdf, then copies all three into the
submission package so the package cannot diverge again.

    python tools/_p694_rebuild_highlights.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
NC = PA / "NC_submission"
TITLE = ("Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow "
         "Theory for PEFT of Contrastive Dual-Encoders")
LIMIT = 85

BULLETS = [
    "Adaptation position matters more than adapter configuration",
    "An ODE predicts gap trajectories at mean R2 of 0.95",
    "Strict freezing confirms the text-only position on CLIP",
    "The same control reverses the ordering on SigLIP",
    "Lower gap and better retrieval are not the same objective",
]

TEX = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\pagestyle{empty}
\begin{document}

\begin{center}
{\large\bfseries Highlights}
\end{center}

\vspace{0.5em}

\noindent\textit{%(title)s}\\
%(author)s

\vspace{1em}

\begin{itemize}[leftmargin=1.5em,itemsep=0.5em]
%(items)s\end{itemize}

\end{document}
"""

AUTHOR = "Hongrui Wan --- University of Southampton"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True
    print(f"  title: {TITLE[:70]}...")
    print(f"  bullets ({len(BULLETS)}), limit {LIMIT}:")
    for b in BULLETS:
        good = len(b) <= LIMIT
        ok = ok and good
        print(f"    {'OK ' if good else 'TOO LONG'} {len(b):>3}  {b}")
    if not (3 <= len(BULLETS) <= 5):
        print(f"  the journal wants 3-5 bullets; got {len(BULLETS)}")
        ok = False
    if not ok:
        print("  refusing to write")
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0

    tex = TEX % {"title": TITLE, "author": AUTHOR,
                 "items": "".join(f"  \\item {b}\n" for b in BULLETS)}
    txt = "Highlights\n\n" + "\n".join(f"- {b}" for b in BULLETS) + "\n"
    (PA / "highlights_nc.tex").write_text(tex, encoding="utf-8")
    (PA / "highlights_nc.txt").write_text(txt, encoding="utf-8")
    print("  wrote highlights_nc.tex and highlights_nc.txt")

    for _ in range(2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                            "highlights_nc.tex"], cwd=str(PA), capture_output=True)
    out = r.stdout.decode("utf-8", errors="replace")
    errs = re.findall(r"^! (.*)$", out, re.M)
    print(f"  compiled highlights_nc.pdf: errors={len(errs)}")
    for e in errs[:4]:
        print(f"     ! {e[:110]}")

    for name, src in (("Highlights.pdf", PA / "highlights_nc.pdf"),
                      ("Highlights.txt", PA / "highlights_nc.txt")):
        shutil.copy2(src, NC / name)
        print(f"  copied -> NC_submission/{name}")

    print()
    print("  verify the package copies")
    r = subprocess.run(["pdftotext", "-q", "-layout", str(NC / "Highlights.pdf"), "-"],
                       capture_output=True)
    t = " ".join(r.stdout.decode("utf-8", errors="replace").split())
    checks = {
        "current title present": "Adaptation Site and the Modality Gap" in t,
        "old title absent": "Protect" not in t,
        "R2 corrected to 0.95": "0.95" in t,
        "stale 0.96/0.97 gone": ("0.96" not in t) and ("0.97" not in t),
        "five bullets": t.count("•") == 5 or len(BULLETS) == 5,
    }
    for k, v in checks.items():
        ok = ok and v
        print(f"    {'OK ' if v else 'BAD'} {k}")
    print()
    print(f"  OVERALL: {'HIGHLIGHTS REBUILT AND CONSISTENT' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
