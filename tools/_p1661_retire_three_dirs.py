"""Retire the three remaining top-level directories into 弃用/ (2026-10-25).

The AGENTS.md "audit scope" rule (2026-10-25) kept `_archive/`, `paper/` and `paper_review/` at the
repository root because an earlier guard matched their names as **naive substrings**. That guard
produced a false positive: every `_archive/` hit it found was `SUBMISSION/_archive/...`, a different
and frozen path. This script re-checks with **root-anchored** matching and then moves the three
directories.

Re-check result driving the move (2026-10-25, base interpreter, 15,111 text files scanned):

  * `_archive/`     - 0 root-anchored references in the 53-script gate chain; the 46 occurrences in
                      `tools/paper_audit/profiles.py` and the five `tools/paper_audit/freeze/*.json`
                      manifests are all `SUBMISSION/_archive/...` => move, no reference update needed.
  * `paper/`        - 1 root-anchored reference inside the active trees (`paper3/README_是哪篇.md`
                      line 12, prose) plus prose in the frozen `SUBMISSION/_archive/*/README.md`
                      files, which the freeze rule forbids editing => update the live one, move, and
                      record the frozen prose as a historical record.
  * `paper_review/` - live references in `paper_review_prl/{MANUSCRIPT.md,DRAFT_OUTLINE.md,
                      FIXES_2026-10-18.md}` and `docs/commentary_compression_and_table.md`
                      => update them, then move.

Destinations: `弃用/08_历史归档/_archive/`, `弃用/06_归档稿件/paper/`, `弃用/06_归档稿件/paper_review/`.

Idempotent: a directory whose source is gone and whose destination exists is skipped.

Usage:
    python tools/_p1661_retire_three_dirs.py [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MOVES = [
    ("_archive", "弃用/08_历史归档/_archive", 251),
    ("paper", "弃用/06_归档稿件/paper", 111),
    ("paper_review", "弃用/06_归档稿件/paper_review", 30),
]
NEW_REVIEW = "弃用/06_归档稿件/paper_review"
NEW_PAPER = "弃用/06_归档稿件/paper"

# (file, old literal, new literal, why) - live references only
REF_EDITS = [
    ("paper_review_prl/MANUSCRIPT.md",
     "引用 key 取自 `paper_review/refs_all.json`（已核验）",
     "引用 key 取自 `%s/refs_all.json`（已核验）" % NEW_REVIEW,
     "Commentary MANUSCRIPT.md:3"),
    ("paper_review_prl/MANUSCRIPT.md",
     "见 `docs/` 与 `paper_review/sections/evidence.md` 的核验记录",
     "见 `docs/` 与 `%s/sections/evidence.md` 的核验记录" % NEW_REVIEW,
     "Commentary MANUSCRIPT.md:4"),
    ("paper_review_prl/DRAFT_OUTLINE.md",
     "只用 `paper_review/refs_all.json` 里已核验的 key",
     "只用 `%s/refs_all.json` 里已核验的 key" % NEW_REVIEW,
     "Commentary DRAFT_OUTLINE.md:16"),
    ("paper_review_prl/FIXES_2026-10-18.md",
     "`paper_review/refs_all.json` (144 entries)",
     "`%s/refs_all.json` (144 entries)" % NEW_REVIEW,
     "Commentary FIXES:96"),
    ("paper_review_prl/FIXES_2026-10-18.md",
     "`paper_review/refs_all.json`",
     "`%s/refs_all.json`" % NEW_REVIEW,
     "Commentary FIXES:111 (any remaining)"),
    ("docs/commentary_compression_and_table.md",
     "`paper_review/sections/taxonomy.md`",
     "`%s/sections/taxonomy.md`" % NEW_REVIEW,
     "commentary working note, line 493"),
    ("paper3/README_是哪篇.md",
     "另有 `paper/`、`paper_ICLR_backup/`（各 12 页）",
     "另有 `paper/`（已移入 `%s/`）、`paper_ICLR_backup/`（各 12 页）" % NEW_PAPER,
     "P3 README prose listing, line 12"),
]


def count_files(p: Path) -> int:
    return sum(1 for _ in p.rglob("*") if _.is_file())


def inventory(p: Path) -> dict:
    out = {}
    for f in p.rglob("*"):
        if f.is_file():
            out[f.relative_to(p).as_posix()] = (f.stat().st_size,
                                                hashlib.sha256(f.read_bytes()).hexdigest())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rc = 0

    print("== preconditions ==")
    todo = []
    for src, dst, expected in MOVES:
        s, d = REPO / src, REPO / dst
        if not s.is_dir():
            if d.is_dir():
                print("  [skip] %-14s already moved (destination has %d files)"
                      % (src, count_files(d)))
            else:
                print("  [FAIL] %-14s source and destination both missing" % src)
                rc = 2
            continue
        n = count_files(s)
        if d.exists():
            print("  [FAIL] %-14s destination exists, refusing to merge" % src)
            rc = 2
            continue
        print("  [ok]   %-14s %d files (expected %d) -> %s" % (src, n, expected, dst))
        if n != expected:
            print("  [FAIL] file count mismatch for %s" % src)
            rc = 2
        todo.append((s, d, n))

    if rc != 0:
        print("\nrefusing to proceed: precondition failure")
        return rc

    # ---- reference updates first (they point at the pre-move paths) ----
    print("\n== live reference updates ==")
    for rel, old, new, why in REF_EDITS:
        p = REPO / rel
        if not p.is_file():
            print("  [FAIL] missing %s" % rel)
            rc = 2
            continue
        text = io.open(p, encoding="utf-8").read()
        if new in text:
            print("  [skip] %-46s already updated (%s)" % (rel, why))
            continue
        n = text.count(old)
        if n < 1:
            print("  [FAIL] %-46s pattern not found (%s)" % (rel, why))
            rc = 2
            continue
        print("  [edit] %-46s %d occurrence(s) (%s)" % (rel, n, why))
        if args.apply:
            io.open(p, "w", encoding="utf-8", newline="\n").write(text.replace(old, new))

    # ---- frozen references: verify they exist, never edit ----
    print("\n== frozen references (NOT edited, freeze rule) ==")
    frozen = 0
    for p in (REPO / "SUBMISSION").rglob("README.md") if (REPO / "SUBMISSION").is_dir() else []:
        try:
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for lit in ("paper/", "_archive/", "paper_review/"):
            if lit in t:
                frozen += 1
                print("  frozen prose mentions %-14r in %s"
                      % (lit, p.relative_to(REPO).as_posix()))
    if frozen == 0:
        print("  none")

    if not args.apply:
        print("\n(preview; pass --apply to update references and move)")
        return rc

    # ---- move ----
    print("\n== move ==")
    for s, d, n in todo:
        before = inventory(s)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        after = inventory(d)
        same = before == after
        print("  %-14s -> %-34s %d files, content identical: %s"
              % (s.name, d.relative_to(REPO).as_posix(), len(after), same))
        if not same:
            print("  [FAIL] content changed during the move")
            rc = 2
        if s.exists():
            print("  [FAIL] source still present: %s" % s)
            rc = 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
