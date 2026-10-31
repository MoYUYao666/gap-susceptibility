# -*- coding: utf-8 -*-
r"""Switch every DOI reference from 23341083 to 23341223 (the operator's choice).

The operator picked 10.5281/zenodo.23341223: it is what the GitHub repository page displays
and it was minted from the public-repository state, so its snapshot is the current one.

Per the tag-freeze rule (AGENTS.md), this changes only main -- the tag and the GitHub
Release are left untouched.

    python tools/_p630_switch_doi.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "doi_switch.json"
OLD = "10.5281/zenodo.23341083"
NEW = "10.5281/zenodo.23341223"

ROOTS = ["paper3", "SUBMISSION", "publish_clean", "README.md"]
SKIP_DIRS = {".git", "__pycache__", "_removed_from_publish", ".worktrees", "backups"}
EXTS = {".tex", ".md", ".txt", ".bib", ".json", ".py"}


def targets() -> list[Path]:
    out = []
    for root in ROOTS:
        p = REPO / root
        if p.is_file():
            out.append(p)
            continue
        for q in p.rglob("*"):
            if (q.is_file() and q.suffix.lower() in EXTS
                    and not any(s in q.parts for s in SKIP_DIRS)):
                out.append(q)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(f"  {OLD}  ->  {NEW}")
    print()
    changed = []
    for p in targets():
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        n = t.count(OLD)
        if not n:
            continue
        rel = p.relative_to(REPO).as_posix()
        print(f"  {n:>2}x  {rel}")
        changed.append((p, rel, n))
    print()
    print(f"  {len(changed)} file(s), {sum(n for _, _, n in changed)} occurrence(s)")
    if not changed:
        print("  nothing to do")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0
    for p, rel, n in changed:
        bak = p.with_suffix(p.suffix + ".bak_p630")
        if not bak.exists():
            shutil.copy2(p, bak)
        t = io.open(p, encoding="utf-8", errors="strict").read()
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    print(f"  Replaced in {len(changed)} file(s).")
    print()
    print("  Re-check (any stale DOI left?):")
    stale = []
    for p in targets():
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        if OLD in t:
            stale.append(p.relative_to(REPO).as_posix())
    print(f"    stale occurrences: {len(stale)}")
    for s in stale:
        print(f"      {s}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"old": OLD, "new": NEW,
             "files": [{"file": r, "count": n} for _, r, n in changed],
             "stale": stale}, ensure_ascii=False, indent=1))
        print(f"\n  Wrote {OUT.relative_to(REPO)}")
    return 0 if not stale else 1


if __name__ == "__main__":
    raise SystemExit(main())
