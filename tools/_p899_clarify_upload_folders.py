# -*- coding: utf-8 -*-
r"""Clarify the two upload folders in the P3 revision package.

The package has an `UPLOAD/` folder from the 13 October submission. Today's replacement files were
staged in `UPLOAD_2026-10-15/`. Two folders named "upload" invite the wrong one being used, so each gets
a one-line pointer at the top saying what it is for.

    python tools/_p899_clarify_upload_folders.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REV = REPO / "SUBMISSION" / "P3_PRL_revision"

NEW_BANNER = (
    "NOTE (2026-10-15): these are the files as SUBMITTED on 2026-10-13.\n"
    "For the pending replacement, use ../UPLOAD_2026-10-15/ instead.\n"
    "\n"
)

OLD_BANNER = (
    "NOTE (2026-10-15): this folder holds the REPLACEMENT files prepared today, with their ordinary\n"
    "names, for upload once the Editorial Office agrees to the replacement requested on 2026-10-15.\n"
    "The versions submitted on 2026-10-13 are in ../UPLOAD/ and are unchanged.\n"
    "\n"
)


def patch(path: Path, banner: str, flag: str) -> None:
    if not path.exists():
        print(f"  {path.name}: not present, skipped")
        return
    t = io.open(path, encoding="utf-8").read()
    if flag in t:
        print(f"  {path.name}: already annotated")
        return
    io.open(path, "w", encoding="utf-8", newline="").write(banner + t)
    print(f"  {path.name}: annotated")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    patch(REV / "UPLOAD" / "README_UPLOAD.txt",
          NEW_BANNER.replace("these are the files as SUBMITTED on 2026-10-13",
                             "these are the files as SUBMITTED on 2026-10-13"), "submitted on 2026-10-13.")
    patch(REV / "UPLOAD_2026-10-15" / "README.md", OLD_BANNER, "REPLACEMENT files prepared today")
    # make sure both pointers agree on the sent date
    for p in (REV / "UPLOAD" / "README_UPLOAD.txt", REV / "UPLOAD_2026-10-15" / "README.md"):
        if p.exists():
            t = io.open(p, encoding="utf-8").read()
            print(f"  {p.parent.name}/{p.name}: mentions 2026-10-13 = {'2026-10-13' in t}, "
                  f"mentions 2026-10-15 = {'2026-10-15' in t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
