# -*- coding: utf-8 -*-
r"""Sync the DOI-updated files into the revision package and rebuild the source archive.

The rebuild is needed because main.pdf and the cover letter changed (DOI inserted). The
package also accumulated .bak_* files inside latex_source/, which must not ship to the
editorial office, so they are removed from the package (they stay in the live tree).

    python tools/_p623_sync_doi_package.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper3" / "paper_ieee"
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
OUT = REPO / "outputs" / "analysis" / "doi_package_sync.json"

COPIES = [
    (PAPER / "main.pdf", PKG / "manuscript" / "main.pdf", "manuscript/main.pdf"),
    (PAPER / "cover_letter_prl.pdf", PKG / "manuscript" / "cover_letter.pdf", "manuscript/cover_letter.pdf"),
    (PAPER / "supplementary" / "supplementary.pdf",
     PKG / "manuscript" / "supplementary.pdf", "manuscript/supplementary.pdf"),
]

# files that belong in the LaTeX source archive handed to the publisher
SOURCE_MEMBERS = ["main.tex", "main_body_full.tex", "main_full.tex", "references.bib"]
ZIP_NAME = "P3_latex_source_revision.zip"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {"copies": [], "removed_backups": [], "zip": {}}

    print("  1) copy rebuilt PDFs into the package")
    for src, dst, label in COPIES:
        if not src.exists():
            print(f"     MISSING source {src}")
            continue
        same = dst.exists() and dst.read_bytes() == src.read_bytes()
        print(f"     {label:<34} {'already current' if same else 'updating'}  "
              f"({src.stat().st_size:,} bytes)")
        if a.apply and not same:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        report["copies"].append({"label": label, "bytes": src.stat().st_size,
                                 "was_current": same})

    lsrc = PKG / "manuscript" / "latex_source"
    print()
    print("  2) remove editor-facing .bak_* files from the package")
    baks = sorted(lsrc.glob("*.bak*"))
    for b in baks:
        print(f"     removing {b.name}")
        if a.apply:
            b.unlink()
        report["removed_backups"].append(b.name)
    print(f"     {len(baks)} removed (the live copies under paper3/ are untouched)")

    print()
    print("  3) source archive: NOT rebuilt here")
    print("     Use tools/_p624_rebuild_source_zip.py, which derives the member list from")
    print("     main.tex and produces the complete archive. An earlier version of this script")
    print("     wrote a four-file archive that could not compile, so it no longer writes one.")
    zpath = PKG / "manuscript" / ZIP_NAME
    present = [m for m in SOURCE_MEMBERS if (lsrc / m).exists()]
    missing = [m for m in SOURCE_MEMBERS if not (lsrc / m).exists()]
    if missing:
        print(f"     NOTE: absent from latex_source/: {missing}")
    print(f"     (the archive on disk is the complete one built by _p624)")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
