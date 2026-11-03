# -*- coding: utf-8 -*-
r"""Change the manuscript title to "Zero-Shot Cross-Architecture Rank Allocation from
Gradient Geometry", chosen by the operator.

Why the title changes: the original title promised that gradient structure *predicts* PEFT
design, and the revision withdrew that claim. The new title names what the paper does show -
zero-shot cross-architecture rank allocation from gradient geometry - and makes no claim
about beating baselines.

Every deliverable that carries the title is updated, with the line breaks the surrounding
LaTeX needs. The response letters gain a sentence explaining the change.

    python tools/_p648_retitle.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

NEW = "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry"

# (file, old text, new text)
EDITS = [
    ("paper3/paper_ieee/main.tex",
     r"\title{Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation}",
     rf"\title{{{NEW}}}"),
    ("paper3/paper_ieee/main_full.tex",
     r"\title{Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation (full version)}",
     rf"\title{{{NEW} (full version)}}"),
    ("paper3/paper_ieee/main_10pp.tex",
     r"\title{Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation}",
     rf"\title{{{NEW}}}"),
    ("SUBMISSION/P3_PRL_revision/manuscript/latex_source/main.tex",
     r"\title{Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation}",
     rf"\title{{{NEW}}}"),
    ("paper3/paper_ieee/title_page_prl.tex",
     "{\\large\\bfseries Gradient Structure Laws as Predictors of PEFT Design:}\\\\[2pt]\n"
     "{\\large\\bfseries Zero-Shot Cross-Architecture Rank Allocation}",
     "{\\large\\bfseries Zero-Shot Cross-Architecture Rank}\\\\[2pt]\n"
     "{\\large\\bfseries Allocation from Gradient Geometry}"),
    ("paper3/paper_ieee/supplementary/supplementary.tex",
     "\\title{Supplementary Material for\\\\\n"
     "Gradient Structure Laws as Predictors of PEFT Design:\\\\\n"
     "Zero-Shot Cross-Architecture Rank Allocation}",
     "\\title{Supplementary Material for\\\\\n"
     "Zero-Shot Cross-Architecture Rank Allocation\\\\\n"
     "from Gradient Geometry}"),
    ("paper3/paper_ieee/PRL_submission/highlights.tex",
     r"\noindent\textit{Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation}\\",
     rf"\noindent\textit{{{NEW}}}\\"),
    ("paper3/paper_ieee/PRL_submission/EM_form_fields.txt",
     "Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation",
     NEW),
    ("paper3/paper_ieee/PRL_submission/README.md",
     "Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation",
     NEW),
    ("SUBMISSION/P3_PRL_revision/RELEASE_NOTES.md",
     "**Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture\n> Rank Allocation**",
     f"**{NEW}**"),
    ("paper3/paper_ieee/cover_letter_prl.tex",
     "``\\emph{Gradient Structure Laws as\nPredictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation}''",
     f"``\\emph{{{NEW}}}''"),
]

# a sentence added to the response letters so the editor sees why the title moved
TITLE_NOTE = (
    "\nTitle. The title has changed from \"Gradient Structure Laws as Predictors of PEFT "
    "Design: Zero-Shot Cross-Architecture Rank Allocation\" to \"" + NEW + "\". The revision "
    "withdrew the claim that gradient structure *predicts* PEFT design, so the original title "
    "no longer described the paper. The new title names the result that does hold: a rank "
    "allocation transferred zero-shot across architectures from gradient geometry, with the "
    "limits of that transfer stated in the paper.\n"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(f"  new title: {NEW}")
    print(f"  {len(NEW)} characters / {len(NEW.split())} words")
    print()
    plan = []
    ok = True
    for rel, old, new in EDITS:
        p = REPO / rel
        if not p.exists():
            print(f"  MISSING  {rel}")
            ok = False
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        flag = "OK " if n == 1 else "CHECK"
        if n != 1:
            ok = False
        print(f"  {flag} {rel:<62} matches={n}")
        if n:
            plan.append((p, t.replace(old, new)))
    print()
    if not ok:
        print("  Some anchors did not match exactly once - nothing written.")
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0
    for p, t2 in plan:
        bak = p.with_suffix(p.suffix + ".bak_p648")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
    print(f"  wrote {len(plan)} file(s)")

    # explain the change in the three response boxes and the combined letter
    print()
    print("  adding the title-change note to the response material:")
    resp = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
    for name in ("P3_RESPONSE_Reviewer1_plain.txt", "P3_RESPONSE_Reviewer2_plain.txt",
                 "P3_RESPONSE_Reviewer3_plain.txt", "P3_RESPONSE_LETTER.md",
                 "P3_RESPONSE_LETTER.txt", "P3_RESPONSE_Reviewer1.txt",
                 "P3_RESPONSE_Reviewer2.txt", "P3_RESPONSE_Reviewer3.txt"):
        p = resp / name
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if "The title has changed from" in t:
            print(f"    already noted  {name}")
            continue
        bak = p.with_suffix(p.suffix + ".bak_p648")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + TITLE_NOTE)
        print(f"    noted          {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
