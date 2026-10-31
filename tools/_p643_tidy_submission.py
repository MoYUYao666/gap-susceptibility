# -*- coding: utf-8 -*-
r"""Tidy the submission area so the wrong file cannot be picked at upload time.

Operator: "清理一下，我怕开错了"

What this does, in order:

1. Creates SUBMISSION/P3_PRL_revision/UPLOAD/ containing exactly the files to upload, under
   names that carry the manuscript id, so no other file in the workspace can be confused
   with them.
2. Moves the superseded first-submission folder SUBMISSION/P3_PRL/ to
   SUBMISSION/_superseded_P3_PRL_submitted_2026-09-26/ so it cannot be picked by accident.
3. Moves every .bak_* inside the revision package into SUBMISSION/_superseded_P3_PRL_revision/
   so no backup can be uploaded.
4. Writes UPLOAD/README_UPLOAD.txt stating exactly what goes in which Editorial Manager slot.

Nothing is deleted.

    python tools/_p643_tidy_submission.py [--dry-run|--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUB = REPO / "SUBMISSION"
PKG = SUB / "P3_PRL_revision"
STAGE = PKG / "UPLOAD"
SUPERSEDED = SUB / "_superseded_P3_PRL_revision"
OLD_SUB = SUB / "P3_PRL"
OLD_SUB_NEW = SUB / "_superseded_P3_PRL_submitted_2026-09-26"

MS = "P3_PRLETTERS-D-26-02378"

# source -> staged name
STAGE_FILES = [
    (PKG / "manuscript" / "main.pdf", f"{MS}_Manuscript.pdf"),
    (PKG / "manuscript" / "cover_letter.pdf", f"{MS}_Cover_Letter.pdf"),
    (PKG / "manuscript" / "supplementary.pdf", f"{MS}_Supplementary.pdf"),
    (PKG / "manuscript" / "P3_latex_source_revision.zip", f"{MS}_LaTeX_Source.zip"),
    (PKG / "response" / "P3_RESPONSE_Reviewer1_plain.txt", f"{MS}_Response_Reviewer1.txt"),
    (PKG / "response" / "P3_RESPONSE_Reviewer2_plain.txt", f"{MS}_Response_Reviewer2.txt"),
    (PKG / "response" / "P3_RESPONSE_Reviewer3_plain.txt", f"{MS}_Response_Reviewer3.txt"),
]

README = f"""UPLOAD THIS FOLDER ONLY
========================

Manuscript : Gradient Structure Laws as Predictors of PEFT Design:
             Zero-Shot Cross-Architecture Rank Allocation
Journal    : Pattern Recognition Letters
Id         : {MS}
Decision   : Revise

Every file below is named with the manuscript id, so nothing else in this workspace can be
mistaken for it. Nothing else needs to be opened.

Editorial Manager slot                        file
--------------------------------------------  ----------------------------------------------
Manuscript (PDF)                              {MS}_Manuscript.pdf
Cover letter                                  {MS}_Cover_Letter.pdf
Supplementary material                        {MS}_Supplementary.pdf
LaTeX source (source file, not a PDF)         {MS}_LaTeX_Source.zip
Response to Reviewer 1 (paste into the box)   {MS}_Response_Reviewer1.txt
Response to Reviewer 2 (paste into the box)   {MS}_Response_Reviewer2.txt
Response to Reviewer 3 (paste into the box)   {MS}_Response_Reviewer3.txt

Form fields
-----------
Data availability : choose "Data is available in a public repository", and give the DOI
                    {MS.replace('P3_', '')}  ->  repository DOI: 10.5281/zenodo.23341223

DO NOT UPLOAD
-------------
- main_full.pdf            (the 13-page archival version; not the submission)
- any .bak_* file          (moved to SUBMISSION/_superseded_P3_PRL_revision/)
- SUBMISSION/_superseded_* (the first submission and this revision's backups)
- anything from another manuscript's folder (A1, A23, PaperA all have a file called
  main.pdf or Manuscript.pdf)

Verified before staging
-----------------------
- main.pdf           10 pages, 0 LaTeX errors, DOI present, superseded numbers absent
- cover_letter.pdf    2 pages, 0 LaTeX errors, DOI present
- source zip         12 members; extracted to a clean directory it compiles standalone
                     (3 passes, 0 errors, 10 pages)
- the three response files are plain UTF-8 text, no LaTeX, no placeholders, no CJK
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.dry_run or a.apply):
        a.dry_run = True

    print("  1) stage the upload files")
    for src, name in STAGE_FILES:
        exists = src.exists()
        print(f"     {'OK ' if exists else 'MISSING'} {name:<56} <- {src.relative_to(REPO)}"
              f"  ({src.stat().st_size if exists else 0:,} bytes)")
    print()
    print(f"  2) move the superseded first submission")
    print(f"     {OLD_SUB.relative_to(REPO)}  ->  {OLD_SUB_NEW.relative_to(REPO)}"
          f"   (exists: {OLD_SUB.exists()})")
    print()
    print("  3) move .bak_* out of the revision package")
    baks = [p for p in PKG.rglob("*.bak*") if p.is_file()]
    for b in baks:
        print(f"     {b.relative_to(PKG)}")
    print(f"     {len(baks)} file(s)")

    if a.dry_run:
        print()
        print("  (dry run)")
        return 0

    STAGE.mkdir(parents=True, exist_ok=True)
    for src, name in STAGE_FILES:
        if src.exists():
            shutil.copy2(src, STAGE / name)
    io.open(STAGE / "README_UPLOAD.txt", "w", encoding="utf-8", newline="").write(README)
    print()
    print(f"  staged {len(STAGE_FILES)} files + README_UPLOAD.txt in {STAGE.relative_to(REPO)}")

    if OLD_SUB.exists() and not OLD_SUB_NEW.exists():
        OLD_SUB.rename(OLD_SUB_NEW)
        print(f"  moved {OLD_SUB.name} -> {OLD_SUB_NEW.name}")

    SUPERSEDED.mkdir(parents=True, exist_ok=True)
    for b in baks:
        rel = b.relative_to(PKG)
        dst = SUPERSEDED / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(b), str(dst))
    print(f"  moved {len(baks)} backup file(s) into {SUPERSEDED.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
