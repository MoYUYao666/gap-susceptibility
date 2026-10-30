# -*- coding: utf-8 -*-
r"""Drop the portal/live filename duplicates from Paper A's package, keeping the build reproducible.

`_p1169_refresh_nc_submission.py` copied each auxiliary file twice: once under the portal name (`Cover Letter.pdf`) and
once under its source name (`cover_letter_nc.pdf`). The duplicate adds 3 files and invites drift. This patch makes the
builder copy only the portal names, moves the existing duplicates into SUBMISSION/_archive/duplicates/ (nothing is
deleted), and leaves the package with exactly the files the portal shows.

    python tools/_p1244_dedupe_nc_package.py [--apply]
"""
from __future__ import annotations

import io
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(REPO, "tools", "_p1169_refresh_nc_submission.py")
PKG = os.path.join(REPO, "SUBMISSION", "PaperA_Neurocomputing")
DUP = os.path.join(REPO, "SUBMISSION", "_archive", "duplicates", "PaperA_Neurocomputing_2026-10-18")
DUPS = ["cover_letter_nc.pdf", "highlights_nc.pdf", "highlights_nc.txt"]

OLD = """        for extra, portal_name in (("highlights_nc.pdf", "Highlights.pdf"),
                                   ("highlights_nc.txt", "Highlights.txt"),
                                   ("cover_letter_nc.pdf", "Cover Letter.pdf")):
            src_p = PA / extra
            if src_p.exists():
                shutil.copy2(src_p, OUT / portal_name)
                shutil.copy2(src_p, SRC.parent / extra)
                print(f"    {portal_name} <- {extra}")"""
NEW = """        for extra, portal_name in (("highlights_nc.pdf", "Highlights.pdf"),
                                   ("highlights_nc.txt", "Highlights.txt"),
                                   ("cover_letter_nc.pdf", "Cover Letter.pdf")):
            src_p = PA / extra
            if src_p.exists():
                shutil.copy2(src_p, OUT / portal_name)
                print(f"    {portal_name} <- {extra}")"""


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = io.open(BUILDER, encoding="utf-8").read()
    n = t.count(OLD)
    print(f"  builder duplicate-copy block: {n}")
    assert n == 1

    present = [f for f in DUPS if os.path.exists(os.path.join(PKG, f))]
    print(f"  duplicates present in package: {present}")

    if not a.apply:
        print("  (dry run)")
        return 0

    t = t.replace(OLD, NEW, 1)
    io.open(BUILDER, "w", encoding="utf-8", newline="").write(t)
    print("  builder now writes portal names only")

    if present:
        os.makedirs(DUP, exist_ok=True)
        for f in present:
            shutil.move(os.path.join(PKG, f), os.path.join(DUP, f))
            print(f"  moved duplicate -> _archive/duplicates/PaperA_Neurocomputing_2026-10-18/{f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
