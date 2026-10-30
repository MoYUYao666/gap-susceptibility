# -*- coding: utf-8 -*-
r"""Wrap the DOI paragraph and recompile main.tex and the cover letter.

The DOI replacement left one over-long source line; it is rewrapped for readability. Then
pdflatex is run twice on each document (twice so that \url and cross-references settle).

    python tools/_p621_rebuild_after_doi.py [--apply]
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
PAPER = REPO / "paper3" / "paper_ieee"

OLD = r"""archived on Zenodo under DOI \texttt{10.5281/zenodo.23341083} (\url{https://doi.org/10.5281/zenodo.23341083}). Every number in the
paper can be recomputed from the public datasets and models above, using the per-run
records and analysis scripts in that archive."""

NEW = r"""archived on Zenodo under DOI \texttt{10.5281/zenodo.23341083}
(\url{https://doi.org/10.5281/zenodo.23341083}). Every number in the paper can be
recomputed from the public datasets and models above, using the per-run records and
analysis scripts in that archive."""


def run(args, cwd):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 1. rewrap
    for rel in ("paper3/paper_ieee/main.tex",
                "SUBMISSION/P3_PRL_revision/manuscript/latex_source/main.tex"):
        p = REPO / rel
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(OLD)
        print(f"  rewrap {rel}: matches={n}")
        if n == 1 and a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    if not a.apply:
        print("  (dry run)")
        return 0

    # 2. recompile
    for tex, label in (("main.tex", "main"), ("cover_letter_prl.tex", "cover letter")):
        p = PAPER / tex
        print()
        print(f"  === compiling {label} ({tex}) ===")
        for k in range(2):
            rc, out, err = run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                tex], PAPER)
            tail = [l for l in out.splitlines() if l.startswith("!") or "Output written" in l]
            print(f"    pass {k+1}: rc={rc}")
            for l in tail[:4]:
                print(f"      {l[:110]}")
            if rc != 0:
                print(f"      FAILED - last output lines:")
                for l in out.splitlines()[-12:]:
                    print(f"        {l[:110]}")
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
