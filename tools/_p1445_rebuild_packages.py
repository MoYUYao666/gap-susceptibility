# -*- coding: utf-8 -*-
r"""Rebuild the five revision packages after the provenance appendices changed the page counts.

    python tools/_p1445_rebuild_packages.py --apply
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "tools/_p1336_build_venue_package.py"
PKGS = [
    ["--manuscript", "paper_a1/main.pdf", "--title-page", "paper_a1/title_page.pdf",
     "--cover-letter", "paper_a1/cover_letter_paa_revision.pdf", "--zip-exclude", "cover_letter.tex,cover_letter_paa.tex,cover_letter_paa_revision.tex",
     "--source", "paper_a1", "--figures", "paper_a1/figures",
     "--venue", "Pattern Analysis and Applications (A1)", "--out", "SUBMISSION/_venue_builds/A1_PAA_next"],
    ["--manuscript", "paper3/paper_ieee/main.pdf", "--title-page", "paper3/paper_ieee/title_page_prl.pdf",
     "--cover-letter", "paper3/paper_ieee/cover_letter_prl_resubmission.pdf", "--supplementary", "paper3/paper_ieee/supplementary/supplementary.pdf", "--source", "paper3/paper_ieee",
     "--figures", "paper3/paper_ieee/figures", "--venue", "Pattern Recognition Letters (P3)",
     "--out", "SUBMISSION/_venue_builds/P3_PRL_next"],
    ["--manuscript", "paper_a2/main_ieee.pdf", "--abstract", "paper_a2/abstract.pdf",
     "--cover-letter", "paper_a2/cover_letter.pdf", "--highlights", "paper_a2/highlights.pdf",
     "--source", "paper_a2", "--figures", "paper_a2/figures", "--venue", "IEEE JOE (A23)",
     "--out", "SUBMISSION/_venue_builds/A23_JOE_next"],
    ["--manuscript", "paper_review_prl/main_prl.pdf", "--cover-letter", "paper_review_prl/cover_letter.pdf",
     "--highlights", "paper_review_prl/highlights.pdf", "--source", "paper_review_prl",
     "--figures", "paper_review_prl/figures", "--venue", "Pattern Recognition Letters (Commentary)",
     "--out", "SUBMISSION/_venue_builds/Commentary_PRL_next"],
    ["--manuscript", "paper合/main_nc.pdf", "--abstract", "paper合/abstract_nc.pdf",
     "--cover-letter", "paper合/cover_letter_nc.pdf", "--highlights", "paper合/highlights_nc.pdf",
     "--source", "paper合", "--figures", "paper合/figures", "--venue", "Neurocomputing (Paper A)",
     "--out", "SUBMISSION/_venue_builds/PaperA_Neurocomputing_next"],
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for args in PKGS:
        if not a.apply:
            print("  would build", args[args.index("--out") + 1])
            continue
        out = os.path.join(REPO, args[args.index("--out") + 1])
        if os.path.isdir(out):
            shutil.rmtree(out)
        r = subprocess.run([sys.executable, B] + args + ["--apply"], cwd=REPO, capture_output=True, text=True)
        print("  package:", args[args.index("--out") + 1], "exit", r.returncode)
        if r.returncode != 0:
            print((r.stdout or "")[-500:], (r.stderr or "")[-500:])
    if a.apply:
        supp_src = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.pdf")
        supp_dst = os.path.join(REPO, "SUBMISSION", "_venue_builds", "P3_PRL_next", "Supplementary.pdf")
        if os.path.exists(supp_src):
            shutil.copy2(supp_src, supp_dst)
            print("  copied supplementary ->", os.path.relpath(supp_dst, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
