# -*- coding: utf-8 -*-
r"""Show the context of every occurrence of the old title in deliverables.

The title is changing, and where it appears matters: a title in \title{} is a metadata field,
but a title inside a highlights bullet or a cover-letter sentence carries prose around it.

    python tools/_p647_show_title_context.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OLD = "Gradient Structure Laws as Predictors of PEFT Design"

TARGETS = [
    "paper3/paper_ieee/main.tex",
    "paper3/paper_ieee/main_full.tex",
    "paper3/paper_ieee/main_10pp.tex",
    "paper3/paper_ieee/title_page_prl.tex",
    "paper3/paper_ieee/cover_letter_prl.tex",
    "paper3/paper_ieee/supplementary/supplementary.tex",
    "paper3/paper_ieee/PRL_submission/highlights.tex",
    "paper3/paper_ieee/PRL_submission/highlights.txt",
    "paper3/paper_ieee/PRL_submission/EM_form_fields.txt",
    "paper3/paper_ieee/PRL_submission/README.md",
    "SUBMISSION/P3_PRL_revision/manuscript/latex_source/main.tex",
    "SUBMISSION/P3_PRL_revision/RELEASE_NOTES.md",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  MISSING  {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        idx = [m.start() for m in re.finditer(re.escape(OLD), t)]
        print("=" * 100)
        print(f"{rel}   ({len(idx)} occurrence(s))")
        print("=" * 100)
        for i in idx:
            seg = " ".join(t[max(0, i - 200):i + 260].split())
            print(f"  ...{seg[:440]}...")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
