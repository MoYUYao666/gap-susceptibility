# -*- coding: utf-8 -*-
r"""Reference the retrieval subsection from the Discussion and add the graphical abstract to the PAA package.

    python tools/_p1278_final_wiring.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
PKG = os.path.join(REPO, "SUBMISSION", "A1_PatternAnalysisApplications")
GA = os.path.join(REPO, "paper_a1", "figures", "graphical_abstract.pdf")

ANCHOR = ("for classification-oriented adaptation in the settings we test, order preservation $\\tau$ is the more "
          "informative of the two signals; centroid-based pipelines need neither.")
ADD = (" On retrieval neither signal transfers out of the box (Section~\\ref{sec:retrieval}), which is the scope "
       "limit we report in that subsection.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    n = t.count(ANCHOR)
    print(f"  discussion anchor: {n}")
    assert n == 1
    t = t.replace(ANCHOR, ANCHOR + ADD, 1)
    print(f"  sec:retrieval references: {t.count('ref{sec:retrieval}')} (label separate)")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  manuscript updated")

    if os.path.exists(GA):
        dst = os.path.join(PKG, "Graphical Abstract.pdf")
        shutil.copy2(GA, dst)
        print("  copied graphical abstract to the package")
        readme = os.path.join(PKG, "README.md")
        r = io.open(readme, encoding="utf-8").read()
        if "Graphical Abstract" not in r:
            lines = r.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("| LaTeX source"):
                    lines.insert(i, "| Graphical abstract (optional) | `Graphical Abstract.pdf` | 1 page; four-panel summary |")
                    break
            io.open(readme, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
            print("  package README updated")
    else:
        print("  !! graphical abstract PDF missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
