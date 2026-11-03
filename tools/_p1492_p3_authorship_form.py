# -*- coding: utf-8 -*-
r"""Add the PRL Authorship Confirmation to the P3 package and the submission record.

    python tools/_p1492_p3_authorship_form.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import glob
import io
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(REPO, "tools", "_p1336_build_venue_package.py")
REBUILD = os.path.join(REPO, "tools", "_p1445_rebuild_packages.py")
SRC = glob.glob(os.path.join(REPO, "paper3", "paper_ieee", "PRL_submission", "Authorship Confirmation (*resubmission*).pdf"))
BUILD = os.path.join(REPO, "SUBMISSION", "_venue_builds", "P3_PRL_next")
RESUB = os.path.join(REPO, "SUBMISSION", "P3_PRL_resubmission")
CHECKLIST = os.path.join(REPO, "docs", "P3_EM_SUBMISSION_CHECKLIST_2026-10-21.md")
EMF = os.path.join(RESUB, "EM_FIELDS.md")


def patch_builder() -> None:
    t = io.open(BUILDER, encoding="utf-8").read()
    if "--authorship" in t:
        return
    t = t.replace('    ap.add_argument("--supplementary", default=None, help="supplementary PDF to copy into the package")',
                  '    ap.add_argument("--supplementary", default=None, help="supplementary PDF to copy into the package")\n'
                  '    ap.add_argument("--authorship", default=None, help="authorship-confirmation PDF to copy")', 1)
    t = t.replace('    if a.supplementary:\n        items.append(("supplementary", abs_(a.supplementary), "Supplementary.pdf"))',
                  '    if a.supplementary:\n        items.append(("supplementary", abs_(a.supplementary), "Supplementary.pdf"))\n'
                  '    if a.authorship:\n        items.append(("authorship", abs_(a.authorship), "AuthorshipConfirmation.pdf"))', 1)
    t = t.replace("| Supplementary | `{supp_name}` | {supp_note} |",
                  "| Supplementary | `{supp_name}` | {supp_note} |\n| Authorship | `{auth_name}` | {auth_note} |", 1)
    t = t.replace('        supp_note=(f"{facts[\'supplementary\'][\'pages\']} pages" if facts.get("supplementary") else "not supplied"),',
                  '        supp_note=(f"{facts[\'supplementary\'][\'pages\']} pages" if facts.get("supplementary") else "not supplied"),\n'
                  '        auth_name=facts["authorship"]["file"] if facts.get("authorship") else "-",\n'
                  '        auth_note=(f"{facts[\'authorship\'][\'pages\']} pages" if facts.get("authorship") else "not supplied"),', 1)
    io.open(BUILDER, "w", encoding="utf-8", newline="").write(t)
    ast.parse(t)
    print("  builder supports --authorship")
    r = io.open(REBUILD, encoding="utf-8").read()
    if SRC:
        old = '"--cover-letter", "paper3/paper_ieee/cover_letter_prl_resubmission.pdf",'
        new = ('"--cover-letter", "paper3/paper_ieee/cover_letter_prl_resubmission.pdf", "--authorship", '
               + repr(SRC[0]).replace("'", '"') + ",")
        if "--authorship" not in r and old in r:
            r = r.replace(old, new, 1)
            io.open(REBUILD, "w", encoding="utf-8", newline="").write(r)
            print("  rebuild script updated")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not SRC:
        print("  authorship PDF missing; run _make_prl_authorship_form first")
        return 1
    src = SRC[0]
    if a.apply:
        patch_builder()
        r = subprocess.run([sys.executable, REBUILD, "--apply"], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        print((r.stdout or "")[-200:])
        for d in (BUILD, RESUB):
            os.makedirs(d, exist_ok=True)
            shutil.copy2(src, os.path.join(d, "AuthorshipConfirmation.pdf"))
        print("  authorship form copied to build and submission packages")
        # README in the submission record
        rp = os.path.join(RESUB, "README.md")
        t = io.open(rp, encoding="utf-8").read()
        if "AuthorshipConfirmation" not in t:
            t = t.replace("| Highlights | `Highlights.pdf` | 5 bullets, <=85 characters |",
                          "| Highlights | `Highlights.pdf` | 5 bullets, <=85 characters |\n"
                          "| Authorship | `AuthorshipConfirmation.pdf` | PRL Confirmation of Authorship (signed, dated) |", 1)
            io.open(rp, "w", encoding="utf-8", newline="").write(t)
            print("  submission README updated")
        # EM fields file table
        t = io.open(EMF, encoding="utf-8").read()
        if "AuthorshipConfirmation.pdf" not in t:
            t = t.replace("| `Highlights.pdf` | Highlights |",
                          "| `Highlights.pdf` | Highlights |\n| `AuthorshipConfirmation.pdf` | Confirmation of Authorship / Authorship statement |", 1)
            io.open(EMF, "w", encoding="utf-8", newline="").write(t)
            print("  EM_FIELDS updated")
        # checklist
        t = io.open(CHECKLIST, encoding="utf-8").read()
        if "AuthorshipConfirmation" not in t:
            t = t.replace("| Highlights | `P3_PRL_next/Highlights.pdf` | 5 条（≤85 字符）|",
                          "| Highlights | `P3_PRL_next/Highlights.pdf` | 5 条（≤85 字符）|\n"
                          "| Authorship | `P3_PRL_next/AuthorshipConfirmation.pdf` | PRL Confirmation of Authorship（新日期 2026-10-21）|")
            io.open(CHECKLIST, "w", encoding="utf-8", newline="").write(t)
            print("  EM checklist updated")
        print("  done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
