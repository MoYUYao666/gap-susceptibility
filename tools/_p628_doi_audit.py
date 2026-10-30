# -*- coding: utf-8 -*-
r"""Audit every place the DOI appears, so a DOI change is a one-command edit.

Written after the operator pointed out that each GitHub Release created a new Zenodo DOI:
the DOI now appears in several artefacts, so there must be a single source of truth for it
and a script that propagates a change everywhere.

    python tools/_p628_doi_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "doi_audit.json"

ROOTS = ["paper3", "SUBMISSION", "publish_clean", "README.md"]
SKIP_DIRS = {".git", "__pycache__", "_removed_from_publish", ".worktrees", "backups"}
EXTS = {".tex", ".md", ".txt", ".bib", ".json", ".py"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hits: dict[str, list[str]] = {}
    for root in ROOTS:
        p = REPO / root
        files = [p] if p.is_file() else [
            q for q in p.rglob("*")
            if q.is_file() and q.suffix.lower() in EXTS
            and not any(s in q.parts for s in SKIP_DIRS)]
        for q in files:
            try:
                t = io.open(q, encoding="utf-8", errors="strict").read()
            except Exception:
                continue
            found = set()
            for m in __import__("re").finditer(r"10\.5281/zenodo\.\d+", t):
                found.add(m.group(0))
            if found:
                hits[q.relative_to(REPO).as_posix()] = sorted(found)
    print("  DOI occurrences:")
    by_doi: dict[str, list[str]] = {}
    for f, dois in sorted(hits.items()):
        print(f"    {f}")
        for d in dois:
            print(f"        {d}")
            by_doi.setdefault(d, []).append(f)
    print()
    print("  DOI -> files:")
    for d, fs in sorted(by_doi.items()):
        print(f"    {d}: {len(fs)} file(s)")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"by_file": hits, "by_doi": by_doi}, ensure_ascii=False, indent=1))
        print(f"\n  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
