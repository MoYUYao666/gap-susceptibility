# -*- coding: utf-8 -*-
r"""Establish the current state of paper合 (Paper A), which the operator is about to submit.

Reads, rather than recalls: the submission package, the compiled PDF, the target journal's
requirements as recorded in the guide, the numbers audit, and the handoff's most recent
entries about this paper.

    python tools/_p679_paperhe_status.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "paperhe_status.json"


def newest(p: Path, n: int = 14) -> list[Path]:
    files = [q for q in p.rglob("*") if q.is_file()]
    files.sort(key=lambda q: q.stat().st_mtime, reverse=True)
    return files[:n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("=" * 104)
    print("1. top level of paper合/")
    print("=" * 104)
    for p in sorted(PA.iterdir()):
        if p.is_dir():
            n = len([q for q in p.rglob("*") if q.is_file()])
            print(f"  {p.name + '/':<34} {n:>5} files")
        else:
            print(f"  {p.name:<34} {p.stat().st_size:>8,} bytes")

    print()
    print("=" * 104)
    print("2. main sources and the compiled PDF")
    print("=" * 104)
    for pat in ("main*.tex", "*.pdf", "*.cls", "*.bst"):
        for p in sorted(PA.glob(pat)):
            print(f"  {p.name:<40} {p.stat().st_size:>9,}  "
                  f"{datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M}")

    print()
    print("=" * 104)
    print("3. submission package")
    print("=" * 104)
    for d in ("NC_submission", "submission", "elsevier_submission"):
        q = PA / d
        if q.exists():
            files = sorted(q.rglob("*"))
            print(f"  {d}/  ({len([f for f in files if f.is_file()])} files)")
            for f in files:
                if f.is_file():
                    print(f"     {f.relative_to(q).as_posix():<52} {f.stat().st_size:>9,}")

    print()
    print("=" * 104)
    print("4. most recently modified files under paper合/")
    print("=" * 104)
    for p in newest(PA, 14):
        print(f"  {datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M}  "
              f"{p.relative_to(PA).as_posix():<58} {p.stat().st_size:>9,}")

    print()
    print("=" * 104)
    print("5. sections present")
    print("=" * 104)
    for d in ("sections", "sections_full", "figures"):
        q = PA / d
        if q.exists():
            names = sorted(x.name for x in q.iterdir() if x.is_file())
            print(f"  {d}/  {names}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"exists": PA.exists(),
             "top": sorted(p.name for p in PA.iterdir()) if PA.exists() else []},
            ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
