# -*- coding: utf-8 -*-
r"""Verify the two submitted P3 PDFs on the Desktop against the working tree.

Before asking the editor for permission to replace files, establish exactly what is in the submitted
versions and what would differ. This compares

* `PRLETTERS-D-26-02378_R1.pdf` (the 32-page submission package: title page, authorship form, cover
  letter, 10-page manuscript) against the manuscript as it was before today's edits, taken from git;
* `P3_PRLETTERS-D-26-02378_Supplementary.pdf` against the supplement as it was before today's edits.

    python tools/_p895_verify_submitted.py
"""
from __future__ import annotations

import difflib
import io
import re
import subprocess
from pathlib import Path

import pypdf

REPO = Path(__file__).resolve().parents[1]
DESKTOP = Path(r"C:\Users\hongr\Desktop")
SUB_MAIN = DESKTOP / "PRLETTERS-D-26-02378_R1.pdf"
SUB_SUPP = DESKTOP / "P3_PRLETTERS-D-26-02378_Supplementary.pdf"


def pages_text(pdf: Path) -> list[str]:
    return [(p.extract_text() or "") for p in pypdf.PdfReader(str(pdf)).pages]


def norm(s: str) -> str:
    s = s.replace("\u2013", "--").replace("\u2014", "---").replace("\u2019", "'")
    return re.sub(r"\s+", " ", s)


def git_show(rel: str) -> str:
    r = subprocess.run(["git", "show", "HEAD:" + rel], cwd=REPO, capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def main() -> int:
    # ---- 1. the submission package
    pages = pages_text(SUB_MAIN)
    print(f"=== {SUB_MAIN.name}: {len(pages)} pages")
    for i, p in enumerate(pages[:5], 1):
        head = norm(p).strip()[:80]
        print(f"  p{i}: {head}")
    # locate the manuscript body: it starts after the cover letter
    body = "\n".join(pages[4:])
    print(f"  manuscript body assumed to be pages 5-{len(pages)} ({len(body)} chars)")

    markers = {
        "old pointer S1--S6": "Supplementary Sections S1--S6",
        "sample-size -> S3": "Sample-size robustness (Supplementary Section S3)",
        "second dataset -> S3": "Second dataset (Supplementary Section S3)",
        "rank scaling -> S4": "Rank scaling (Supplementary Section S4)",
        "comparison -> S5": "Comparison with prior work (Supplementary Section S5)",
        "downstream -> S7": "Supplementary Section S7",
    }
    flat = norm(body)
    print("  pointers as printed in the submitted manuscript:")
    for name, m in markers.items():
        print(f"    {'YES' if m in flat else 'no ':>3}  {name}")

    # what changed in the working tree today
    diff = list(difflib.unified_diff(
        norm(git_show("paper3/paper_ieee/main.tex") + git_show("paper3/paper_ieee/sections/experiments.tex")).split(),
        norm((REPO / "paper3" / "paper_ieee" / "main.tex").read_text(encoding="utf-8")
             + (REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex").read_text(encoding="utf-8")).split(),
        lineterm="", n=0))
    changed = [l for l in diff if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    print(f"  working-tree changes to the main text: {len(changed)} token-level line(s)")

    # ---- 2. the submitted supplement
    supp_pages = pages_text(SUB_SUPP)
    supp = norm("\n".join(supp_pages))
    print()
    print(f"=== {SUB_SUPP.name}: {len(supp_pages)} pages, {len(supp)} chars")
    probes = {
        "old: Theorem the main text": "Theorem the main text",
        "old: Table the main text": "Table the main text",
        "old: Table Supplementary Table S4": "Table Supplementary Table S4",
        "old: Table Supplementary Table S3": "Table Supplementary Table S3",
        "old: Table Supplementary Table S2": "Table Supplementary Table S2",
        "old: Figure Supplementary Figure S3": "Figure Supplementary Figure S3",
        "old: Lemma Lemma 1": "Lemma Lemma 1",
        "section count 9 (S1..S9)": None,
    }
    for name, m in probes.items():
        if m is None:
            continue
        print(f"    {'YES' if m in supp else 'no ':>3}  {name}")
    heads = re.findall(r"S(\d)\.\s+[A-Z]", supp)
    print(f"  section headings in the submitted supplement: {sorted(set(heads))}")
    print(f"  tables: {len(re.findall('TABLE S', supp))} references, "
          f"{supp.count('TABLE S5')} of them S5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
