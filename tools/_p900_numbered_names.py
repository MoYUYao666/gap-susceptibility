# -*- coding: utf-8 -*-
r"""Give the replacement files the same names the first upload used.

The 13 October upload in `UPLOAD/` uses manuscript-numbered names
(`P3_PRLETTERS-D-26-02378_Manuscript.pdf`, `..._Supplementary.pdf`). The replacement staged today used
plain `main.pdf` / `supplementary.pdf`, which does not match what the file slots expect. Both namings
are now present in `UPLOAD_2026-10-15/`, byte-identical, so either can be used without a rename.

    python tools/_p900_numbered_names.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REV = REPO / "SUBMISSION" / "P3_PRL_revision"
OLD = REV / "UPLOAD"
NEW = REV / "UPLOAD_2026-10-15"
PAIRS = [
    ("main.pdf", "P3_PRLETTERS-D-26-02378_Manuscript.pdf"),
    ("supplementary.pdf", "P3_PRLETTERS-D-26-02378_Supplementary.pdf"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # confirm the old folder holds the submitted versions and the new one the replacements
    old_m, old_s = OLD / "P3_PRLETTERS-D-26-02378_Manuscript.pdf", OLD / "P3_PRLETTERS-D-26-02378_Supplementary.pdf"
    for p in (old_m, old_s):
        print(f"  submitted copy {p.name}: {p.stat().st_size:,} bytes")
    print(f"  replacement main.pdf and supplementary.pdf differ from them: "
          f"{sha(old_m) != sha(NEW / 'main.pdf') and sha(old_s) != sha(NEW / 'supplementary.pdf')}")

    if not a.apply:
        print("  (dry run)")
        return 0

    for plain, numbered in PAIRS:
        src, dst = NEW / plain, NEW / numbered
        shutil.copy2(src, dst)
        assert sha(src) == sha(dst), f"copy mismatch for {numbered}"
        print(f"  {plain} -> {numbered}  ({dst.stat().st_size:,} bytes)")

    readme = NEW / "README.md"
    t = io.open(readme, encoding="utf-8").read()
    if "Two namings" not in t:
        add = (
            "Two namings of the same two files are here, byte-identical:\n"
            "  main.pdf / supplementary.pdf                              plain\n"
            "  P3_PRLETTERS-D-26-02378_Manuscript.pdf                    manuscript-numbered\n"
            "  P3_PRLETTERS-D-26-02378_Supplementary.pdf                 manuscript-numbered\n"
            "The numbered names match the slots used in the 13 October upload (see ../UPLOAD/).\n"
            "\n"
        )
        io.open(readme, "w", encoding="utf-8", newline="").write(add + t)
        print("  README.md: noted both namings")

    print(f"  folder now holds: {sorted(p.name for p in NEW.iterdir())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
