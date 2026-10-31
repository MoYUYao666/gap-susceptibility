# -*- coding: utf-8 -*-
r"""Remove the markdown asterisks from the title-change note, then rebuild everything.

The note said "the claim that gradient structure *predicts* PEFT design", but these files are
plain text pasted into a web form, where asterisks show literally. The rest of the response
material carries no markdown emphasis, so this keeps that property.

Then: recompile main.tex, cover letter and the supplementary material (all three carry the
title), refresh the staged upload copies, rebuild the source archive, and verify.

    python tools/_p649_fix_note_and_rebuild.py [--apply]
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
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
STAGE = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD"

FIXES = [
    ("gradient structure *predicts* PEFT design", "gradient structure predicts PEFT design"),
    ("names the result that does hold", "names the result that does hold"),
]

DOCS = [
    ("main.tex", "main", 10),
    ("cover_letter_prl.tex", "cover letter", 2),
    ("supplementary/supplementary.tex", "supplementary", 5),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("  1) strip markdown asterisks from the note")
    n_fixed = 0
    for p in sorted(RESP.glob("*")):
        if not p.is_file() or p.suffix.lower() not in (".txt", ".md"):
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if "*predicts*" not in t:
            continue
        t2 = t.replace("*predicts*", "predicts")
        n_fixed += 1
        print(f"     {p.name}")
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(t2)
    print(f"     {n_fixed} file(s)")

    print()
    print("  2) recompile the three documents that carry the title")
    if not a.apply:
        print("     (dry run)")
        return 0
    for tex, label, want in DOCS:
        p = PAPER / tex
        if not p.exists():
            print(f"     MISSING {tex}")
            continue
        passes = []
        for k in range(2):
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                tex], cwd=str(PAPER), capture_output=True)
            out = r.stdout.decode("utf-8", errors="replace")
            errs = re.findall(r"^! (.*)$", out, re.M)
            pages = re.findall(r"Output written on .*?\((\d+) pages", out)
            passes.append((r.returncode, len(errs), pages[0] if pages else None))
        rc, ne, pg = passes[-1]
        flag = "OK " if rc == 0 and ne == 0 else "BAD"
        print(f"     {flag} {label:<16} pages={pg} (want {want})  errors={ne}  rc={rc}")
        if rc != 0:
            for e in errs[:5]:
                print(f"          ! {e[:100]}")

    print()
    print("  3) refresh the staged copies and the source archive")
    pairs = [
        (PAPER / "main.pdf", STAGE / "P3_PRLETTERS-D-26-02378_Manuscript.pdf"),
        (PAPER / "cover_letter_prl.pdf", STAGE / "P3_PRLETTERS-D-26-02378_Cover_Letter.pdf"),
        (PAPER / "supplementary" / "supplementary.pdf",
         STAGE / "P3_PRLETTERS-D-26-02378_Supplementary.pdf"),
    ]
    for src, dst in pairs:
        if src.exists():
            shutil.copy2(src, dst)
            print(f"     staged {dst.name}  ({dst.stat().st_size:,} bytes)")
    for src, dst in pairs:
        # keep the package copies in step as well
        pkg_name = {"P3_PRLETTERS-D-26-02378_Manuscript.pdf": "main.pdf",
                    "P3_PRLETTERS-D-26-02378_Cover_Letter.pdf": "cover_letter.pdf",
                    "P3_PRLETTERS-D-26-02378_Supplementary.pdf": "supplementary.pdf"}[dst.name]
        shutil.copy2(src, REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / pkg_name)
    print("     package copies updated")
    r = subprocess.run([sys.executable, str(REPO / "tools" / "_p624_rebuild_source_zip.py"),
                        "--apply"], cwd=str(REPO), capture_output=True)
    tail = [l for l in r.stdout.decode("utf-8", errors="replace").splitlines()
            if "Wrote P3" in l or "Integrity" in l]
    for l in tail:
        print(f"     {l.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
