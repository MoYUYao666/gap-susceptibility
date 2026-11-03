# -*- coding: utf-8 -*-
r"""Show every broken cross-reference in P3's supplement with enough context to fix it.

    python tools/_p883_p3_broken_refs.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"

PATTERNS = [
    (r"Theorem~[A-Za-z]\w*", "theorem reference"),
    (r"Lemma~[A-Za-z]\w*", "lemma reference"),
    (r"Table~[A-Za-z]\w*", "table reference"),
    (r"Figure~[A-Za-z]\w*", "figure reference"),
]

t = SUPP.read_text(encoding="utf-8", errors="replace")
for pat, kind in PATTERNS:
    for m in re.finditer(pat, t):
        ln = t[: m.start()].count("\n") + 1
        start = t.rfind("\n\n", 0, m.start())
        end = t.find("\n\n", m.end())
        para = t[start:end].strip().replace("\n", " ")
        print(f"--- {kind}: line {ln}  [{m.group(0)}]")
        print(f"    {para[:600]}")
        print()

print("=== tables defined in the supplement, in order ===")
for i, m in enumerate(re.finditer(r"\\begin\{table\*?\}", t), 1):
    ln = t[: m.start()].count("\n") + 1
    cap = re.search(r"\\caption\{([^}]*)\}", t[m.start(): m.start() + 4000])
    lab = re.search(r"\\label\{([^}]*)\}", t[m.start(): m.start() + 4000])
    print(f"  S{i} (line {ln}): label={lab.group(1) if lab else 'NONE'}  "
          f"caption={cap.group(1)[:90] if cap else 'NONE'}")

print()
print("=== theorems / lemmas defined in the supplement ===")
for m in re.finditer(r"\\begin\{(theorem|lemma|corollary|definition|remark)\}(\[[^\]]*\])?", t):
    ln = t[: m.start()].count("\n") + 1
    print(f"  line {ln}: {m.group(0)}")

print()
print("=== figures defined in the supplement ===")
for m in re.finditer(r"\\begin\{figure\*?\}", t):
    ln = t[: m.start()].count("\n") + 1
    lab = re.search(r"\\label\{([^}]*)\}", t[m.start(): m.start() + 3000])
    print(f"  line {ln}: label={lab.group(1) if lab else 'NONE'}")

print()
print("=== main text: theorem and lemma definitions ===")
main = (REPO / "paper3" / "paper_ieee" / "main.tex").read_text(encoding="utf-8", errors="replace")
for p in sorted((REPO / "paper3" / "paper_ieee" / "sections").glob("*.tex")):
    if ".bak" in p.name:
        continue
    mt = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\\begin\{(theorem|lemma|corollary|definition|remark)\}(\[[^\]]*\])?", mt):
        ln = mt[: m.start()].count("\n") + 1
        lab = re.search(r"\\label\{([^}]*)\}", mt[m.start(): m.start() + 1200])
        print(f"  {p.name}:{ln}: {m.group(0)}  label={lab.group(1) if lab else 'NONE'}")
