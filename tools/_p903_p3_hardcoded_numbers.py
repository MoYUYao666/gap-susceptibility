# -*- coding: utf-8 -*-
r"""Find every hard-coded theorem/lemma/corollary reference in P3's main text and supplement.

A number written by hand in the source does not move when a counter moves, and the supplement is
compiled separately so it cannot use \ref into the main text. Before touching the theorem counters,
this lists everything that would have to be updated by hand.

    python tools/_p903_p3_hardcoded_numbers.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
FILES = [P3 / "main.tex", P3 / "supplementary" / "supplementary.tex"] + \
        sorted(p for p in (P3 / "sections").glob("*.tex") if ".bak" not in p.name)

PAT = re.compile(r"(Theorem|Lemma|Corollary|Definition|Proposition|Equation|Eq\.)\s*~?\s*"
                 r"(?:[IVX]+\.)?(\d+)(\.\d+)?")
for p in FILES:
    t = p.read_text(encoding="utf-8", errors="replace")
    hits = []
    for m in PAT.finditer(t):
        # skip the counter declarations themselves and \newtheorem definitions
        if "newtheorem" in t[max(0, m.start() - 60):m.start()]:
            continue
        ln = t[: m.start()].count("\n") + 1
        hits.append((ln, m.group(0).strip()))
    if hits:
        print(f"=== {p.relative_to(REPO).as_posix()}")
        for ln, s in hits:
            print(f"   line {ln:>4}: {s}")
print()
print("=== subsection headings that name a corollary ===")
for p in FILES:
    t = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\\(?:sub)?section\{([^}]*Corollary[^}]*)\}", t):
        ln = t[: m.start()].count("\n") + 1
        print(f"  {p.name}:{ln}: {m.group(1)}")
