# -*- coding: utf-8 -*-
r"""Remove the duplicated subsection headings in the Paper 3 supplementary material.

Four headings appear twice on consecutive lines, which renders as the same title printed twice:

  Comparison with Prior Work
  Rank Scaling and Gamma Evolution
  Second-Dataset Validation (ShareGPT)
  Sample Size Robustness

A fifth title, "Downstream check", also occurs twice but under different sections (Deferred
Experimental Detail and Deferred Downstream and Probe Detail), so it is not a duplicate and is left
alone. Each removal is asserted to be an exact consecutive duplicate before anything is written.

    python tools/_p773_fix_supp_duplicates.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    raw = TARGET.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines(keepends=True)
    print(f"  {TARGET.relative_to(REPO)}: {len(lines)} lines")

    # find every pair of consecutive identical \subsection lines
    dupes = []
    for i in range(len(lines) - 1):
        s1, s2 = lines[i].strip(), lines[i + 1].strip()
        if s1.startswith("\\subsection{") and s1 == s2:
            dupes.append((i, s1))
    print()
    print("=" * 100)
    print("consecutive duplicate subsection headings")
    print("=" * 100)
    for i, txt in dupes:
        print(f"  L{i + 1} and L{i + 2}: {txt}")

    if not dupes:
        print("  none found")
        return 0

    print()
    print("=" * 100)
    print("other repeated headings that are NOT consecutive (left alone)")
    print("=" * 100)
    heads = {}
    for i, l in enumerate(lines):
        m = re.match(r"\s*\\(section|subsection|subsubsection)\*?\{(.*?)\}", l)
        if m:
            heads.setdefault(m.group(2), []).append((i + 1, m.group(1)))
    for name, where in heads.items():
        if len(where) > 1:
            consecutive = any(abs(where[j][0] - where[j + 1][0]) <= 1
                              for j in range(len(where) - 1))
            if not consecutive:
                print(f"  {name!r} at {[w[0] for w in where]} ({where[0][1]}) - not consecutive")

    if not a.apply:
        print()
        print("  (dry run)")
        return 0

    # remove only the second line of each consecutive pair, from the bottom up
    out = list(lines)
    for i, _ in reversed(dupes):
        del out[i + 1]
    new = "".join(out)
    bak = TARGET.with_suffix(".tex.bak_p773")
    if not bak.exists():
        shutil.copy2(TARGET, bak)
    TARGET.write_text(new, encoding="utf-8", newline="")

    print()
    print("=" * 100)
    print("after the fix")
    print("=" * 100)
    chk = TARGET.read_text(encoding="utf-8", errors="replace")
    cl = chk.splitlines()
    remaining = 0
    for i in range(len(cl) - 1):
        if cl[i].strip().startswith("\\subsection{") and cl[i].strip() == cl[i + 1].strip():
            remaining += 1
            print(f"  still duplicated at L{i + 1}: {cl[i].strip()}")
    print(f"  consecutive duplicates remaining: {remaining}")
    print(f"  lines {len(lines)} -> {len(cl)}")

    heads2 = []
    for i, l in enumerate(cl):
        m = re.match(r"\s*\\(?:section|subsection|subsubsection)\*?\{(.*?)\}", l)
        if m:
            heads2.append(m.group(1))
    print(f"  headings: {len(heads)} -> {len(heads2)}")
    print()
    print("  full heading list after the fix:")
    for i, l in enumerate(cl):
        m = re.match(r"\s*\\(section|subsection|subsubsection)\*?\{(.*?)\}", l)
        if m:
            print(f"     L{i + 1:<5} {m.group(1):<13} {m.group(2)[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
