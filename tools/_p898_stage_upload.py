# -*- coding: utf-8 -*-
r"""Stage the replacement P3 files under their normal names, ready to upload.

Operator instruction (2026-10-15): "不用main_corrected.pdf加corrected，正常即可" — the files to upload should
carry their ordinary names, not a "corrected" suffix.

So the two PDFs are copied into `SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/` as `main.pdf` and
`supplementary.pdf`. Nothing is deleted: the copies in `CORRECTED_2026-10-15/` stay where they are, and
the Desktop copies of the submitted versions are untouched. The new folder gets a README that states the
difference and the checks, so the upload folder is self-describing.

    python tools/_p898_stage_upload.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REV = REPO / "SUBMISSION" / "P3_PRL_revision"
SRC = REV / "CORRECTED_2026-10-15"
DST = REV / "UPLOAD_2026-10-15"
PAIRS = [("main_corrected.pdf", "main.pdf"), ("supplementary_corrected.pdf", "supplementary.pdf")]

README = """Upload folder for P3 (PRLETTERS-D-26-02378R1) - prepared 2026-10-15

Two files, under their ordinary names:

  main.pdf            the manuscript, 10 pages
  supplementary.pdf   the Supplementary Material, 5 pages

They replace the versions uploaded on 2026-10-13. What differs:

  main.pdf            five pointers to the Supplementary Material only:
                        Supplementary Sections S1-S6  ->  S1-S9
                        sample-size material          S3  ->  S9
                        second-dataset material       S3  ->  S9
                        rank-scaling material         S4  ->  S5
                        comparison with prior work    S5  ->  S9
                      No sentence, number, table, figure or conclusion changes.

  supplementary.pdf   section order aligned to the manuscript numbering, every internal
                      cross-reference now resolves, and the sample-size table that the
                      supplement promised but did not contain is included (5 tables).
                      The table's caption states the seed count (one) and the epoch count (four).

Checks run on these two files:

  tools/_p893_p3_correspondence.py   -> CORRESPONDENCE VERIFIED
  tools/_p892_p3_build_check.py      -> 0 errors, 0 undefined references, 0 undefined citations
  neither PDF contains a "??" unresolved reference

The versions as submitted are on the Desktop
(PRLETTERS-D-26-02378_R1.pdf, P3_PRLETTERS-D-26-02378_Supplementary.pdf) and are not modified.
Copies of these same two replacement files also sit in ../CORRECTED_2026-10-15/ with descriptive names.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for src_name, _dst in PAIRS:
        p = SRC / src_name
        assert p.exists(), f"missing {p}"
        print(f"  {src_name:<28} {p.stat().st_size:>9,} bytes")
    if not a.apply:
        print("  (dry run)")
        return 0

    DST.mkdir(parents=True, exist_ok=True)
    for src_name, dst_name in PAIRS:
        shutil.copy2(SRC / src_name, DST / dst_name)
        assert (DST / dst_name).stat().st_size == (SRC / src_name).stat().st_size
        print(f"  {src_name} -> UPLOAD_2026-10-15/{dst_name}")
    io.open(DST / "README.md", "w", encoding="utf-8", newline="").write(README)

    listing = sorted(p.name for p in DST.iterdir())
    print(f"  folder now holds: {listing}")

    # remove the "corrected" wording from the archive folder's README so the two folders agree
    old = SRC / "README.md"
    if old.exists():
        t = io.open(old, encoding="utf-8").read()
        t = t.replace("main_corrected.pdf", "main.pdf").replace(
            "supplementary_corrected.pdf", "supplementary.pdf")
        t = t.replace("# Corrected P3 files, 2026-10-15",
                      "# P3 replacement files, 2026-10-15 (descriptive names; upload copies are in ../UPLOAD_2026-10-15/ with normal names)")
        io.open(old, "w", encoding="utf-8", newline="").write(t)
        print("  updated CORRECTED_2026-10-15/README.md to use the normal names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
