# -*- coding: utf-8 -*-
r"""Disambiguate the two subsection headings that repeat across sections of the supplementary.

Four headings were exact consecutive duplicates and have been removed. Two titles remain repeated,
but as different content rather than duplicated content:

  section 7 (Deferred Experimental Detail)            full treatment
  section 9 (Deferred Downstream and Probe Detail)    condensed restatement, whose own body text
                                                      cites "Supplementary Section S7" / "S6"

Because the titles are identical, the rendered heading list still reads as a duplicate. Labelling the
section 9 subsections as summaries removes the ambiguity without altering any claim.

    python tools/_p773b_disambiguate.py [--apply]
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

# (old heading, new heading) - only inside section 9, after the section line for that section
REPLACEMENTS = [
    ("\\subsection{Downstream check}", "\\subsection{Downstream check (summary)}"),
    ("\\subsection{Decoder VLM}", "\\subsection{Decoder VLM (summary)}"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = TARGET.read_text(encoding="utf-8", errors="replace")

    # locate the start of the last section, so only its subsections are renamed
    secs = [(m.start(), m.group(0)) for m in
            re.finditer(r"\\section\{[^}]*\}", t)]
    print(f"  {len(secs)} sections")
    for s, name in secs:
        print(f"     offset {s:>6}  {name}")
    if not secs:
        print("  no sections found")
        return 1
    last_start = secs[-1][0]
    print()
    print(f"  renames apply only after offset {last_start} ({secs[-1][1]})")

    head, tail = t[:last_start], t[last_start:]
    for old, new in REPLACEMENTS:
        n_tail = tail.count(old)
        n_head = head.count(old)
        print(f"  {old:<34} in last section: {n_tail}   earlier: {n_head}")
        if n_tail != 1:
            print("     !! expected exactly one occurrence in the last section")
            return 1
        if not a.apply:
            continue
        tail = tail.replace(old, new)

    if not a.apply:
        print()
        print("  (dry run)")
        return 0

    new_t = head + tail
    bak = TARGET.with_suffix(".tex.bak_p773b")
    if not bak.exists():
        shutil.copy2(TARGET, bak)
    TARGET.write_text(new_t, encoding="utf-8", newline="")

    print()
    print("  headings after the change:")
    for i, l in enumerate(new_t.splitlines(), 1):
        m = re.match(r"\s*\\(section|subsection)\*?\{(.*?)\}", l)
        if m:
            print(f"     L{i:<5} {m.group(1):<11} {m.group(2)[:78]}")

    # duplicate check over the whole file, module-style
    names = re.findall(r"\\(?:section|subsection)\*?\{([^}]*)\}", new_t)
    dupes = {n: names.count(n) for n in set(names) if names.count(n) > 1}
    print()
    print(f"  remaining repeated heading names: {dupes if dupes else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
