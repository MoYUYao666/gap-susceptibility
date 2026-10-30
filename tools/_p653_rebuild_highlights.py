# -*- coding: utf-8 -*-
r"""Rebuild the highlights so they are consistent, compliant and free of withdrawn claims.

Three problems were found, all of which matter because highlights go to the editorial office:

1. highlights.txt was never updated and still advertises withdrawn claims:
   "the unique admissible allocation statistic" (the paper now needs axiom R3'),
   "A critical rank separates safe, damaging and collapsing allocation regimes"
   (the crossing is bracketed at r in [5,6] with permutation p = 0.100),
   "Counterfactual tests show the coupling predicts allocation uncertainty" (the 30x ratio
   was withdrawn; 98.9% of that spread is between-rank variance).
2. The .tex version printed the author name and affiliation. Highlights are not the title
   page, and the operator asked that personal information not go into published artefacts.
3. One bullet was 87 characters, over the 85-character limit.

This writes one bullet list and derives both files from it, so they cannot disagree again.
Character counts are asserted, not eyeballed.

    python tools/_p653_rebuild_highlights.py [--apply]
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
SUB = REPO / "paper3" / "paper_ieee" / "PRL_submission"
TITLE = "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry"
LIMIT = 85

BULLETS = [
    "Cross-modal gradient coupling gives a canonical PEFT allocation statistic",
    "Requiring additivity is an axiom, not a consequence of block decomposability",
    "Measured on CLIP, it predicts a LLaVA rank allocation with no target gradient",
    "The allocation does not beat matched controls; we report that rather than hide it",
    "At matched budget, AdaLoRA reaches lower alignment energy than our allocation",
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

\noindent\textit{%(title)s}

\vspace{1em}

\begin{itemize}[leftmargin=1.5em,itemsep=0.5em]
%(items)s\end{itemize}

\end{document}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(f"  title: {TITLE}")
    print(f"  bullets ({len(BULLETS)}), limit {LIMIT} characters:")
    ok = True
    for i, b in enumerate(BULLETS, 1):
        n = len(b)
        good = n <= LIMIT
        ok = ok and good
        print(f"    {'OK ' if good else 'TOO LONG'} {n:>3}  {b}")
    if len(BULLETS) < 3 or len(BULLETS) > 5:
        print(f"  the journal wants 3-5 bullets; this list has {len(BULLETS)}")
        ok = False
    if not ok:
        print("  refusing to write")
        return 1

    tex = TEX % {"title": TITLE,
                 "items": "".join(f"  \\item {b}\n" for b in BULLETS)}
    txt_lines = ["Highlights", ""]
    for b in BULLETS:
        txt_lines.append(f"- {b}")
    txt = "\n".join(txt_lines) + "\n"

    if not a.apply:
        print()
        print("  (dry run)")
        return 0

    for name, content in (("highlights.tex", tex), ("highlights.txt", txt)):
        p = SUB / name
        bak = p.with_suffix(p.suffix + ".bak_p653")
        if p.exists() and not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(content)
        print(f"  wrote {name}")

    # rebuild the PDF and check it
    for k in range(2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                            "highlights.tex"], cwd=str(SUB), capture_output=True)
        out = r.stdout.decode("utf-8", errors="replace")
    errs = re.findall(r"^! (.*)$", out, re.M)
    pages = re.findall(r"Output written on highlights\.pdf \((\d+) pages", out)
    print(f"  rebuilt highlights.pdf: pages={pages[0] if pages else '?'} errors={len(errs)}")

    r = subprocess.run(["pdftotext", "-q", "-layout", str(SUB / "highlights.pdf"), "-"],
                       capture_output=True)
    t = r.stdout.decode("utf-8", errors="replace")
    flat = re.sub(r"[\s\u00ad]+", "", t)
    print()
    print("  PDF checks:")
    checks = {
        "new title present": "Zero-ShotCross-ArchitectureRankAllocation" in flat,
        "old title absent": "GradientStructureLaws" not in flat,
        "no author name": "Hongrui" not in flat,
        "no affiliation": "Southampton" not in flat,
        "no 'unique admissible'": "uniqueadmissible" not in flat.lower(),
        "no 'critical rank separates'": "criticalrankseparates" not in flat.lower(),
    }
    for k, v in checks.items():
        print(f"    {'OK ' if v else 'BAD'} {k}")
        ok = ok and v
    print()
    print(f"  OVERALL: {'ALL CHECKS PASSED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
