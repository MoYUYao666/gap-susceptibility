# -*- coding: utf-8 -*-
r"""Inventory every file that could be mistaken for a submission slot file.

The operator is about to upload to Editorial Manager and asked for the workspace to be
tidied so the wrong file cannot be picked. Before moving anything, list every candidate
for each slot, with size and modification time, so the plan is made on facts.

    python tools/_p642_submission_inventory.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "submission_inventory.json"

# which file names could plausibly be mistaken for which slot
SLOTS = {
    "manuscript PDF": [r"^main\.pdf$", r"^main_10pp\.pdf$", r"^manuscript.*\.pdf$"],
    "full / archived PDF": [r"^main_full\.pdf$", r"^main_7pp.*\.pdf$"],
    "cover letter": [r"cover.*letter.*\.pdf$", r"cover.*letter.*\.docx$", r"^Cover.*\.docx$"],
    "supplementary": [r"^supplementary.*\.pdf$", r"^supp.*\.pdf$"],
    "title page": [r"title.*page.*\.pdf$", r"title.*page.*\.docx$"],
    "highlights": [r"highlights?.*\.pdf$", r"highlights?.*\.docx$"],
    "declarations": [r"declaration.*\.(pdf|docx)$"],
    "source archive": [r"latex_source.*\.zip$", r"source.*\.zip$"],
    "reviewer / old material": [r"^Reviewer\.pdf$", r"reviews?.*\.pdf$"],
}

SKIP = {".git", "_removed_from_publish", "__pycache__", ".worktrees", "backups",
        "_bak_archive", "tools"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    found: dict[str, list[tuple[str, int, str]]] = {k: [] for k in SLOTS}
    for p in REPO.rglob("*"):
        if not p.is_file():
            continue
        if any(s in p.parts for s in SKIP):
            continue
        for slot, pats in SLOTS.items():
            if any(re.search(pat, p.name, re.I) for pat in pats):
                found[slot].append(
                    (p.relative_to(REPO).as_posix(), p.stat().st_size,
                     __import__("datetime").datetime.fromtimestamp(
                         p.stat().st_mtime).strftime("%m-%d %H:%M")))
    print(f"  candidates for each submission slot\n")
    for slot, rows in found.items():
        if not rows:
            continue
        print("=" * 100)
        print(f"{slot}  ({len(rows)} candidate{'s' if len(rows) != 1 else ''})")
        print("=" * 100)
        for name, size, mt in sorted(rows):
            flag = "  <-- COLLISION RISK" if len(rows) > 1 else ""
            print(f"  {size:>10,}  {mt}  {name}{flag}")
        print()
    # also list the package's own directory in full: that is what gets uploaded
    pkg = REPO / "SUBMISSION" / "P3_PRL_revision"
    print("=" * 100)
    print("The revision package as it stands (this is what should be uploaded from)")
    print("=" * 100)
    for p in sorted(pkg.rglob("*")):
        if p.is_file():
            print(f"  {p.stat().st_size:>10,}  {p.relative_to(pkg).as_posix()}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {k: [{"file": f, "bytes": s, "mtime": m} for f, s, m in v]
             for k, v in found.items()}, ensure_ascii=False, indent=1))
        print()
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
