# -*- coding: utf-8 -*-
r"""Report the LaTeX warnings in P3's main log and show the corollary subsections.

    python tools/_p904_p3_warnings.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
log = (P3 / "main.log").read_text(encoding="utf-8", errors="replace")

print("=== multiply-defined labels ===")
mult = re.findall(r"Label `([^']+)' multiply defined", log)
print(f"  {len(mult)}: {sorted(set(mult))}")

print()
print("=== hyperref warnings ===")
for m in re.findall(r"Package hyperref Warning: [^\n]*", log)[:6]:
    print(f"  {m[:118]}")

print()
print("=== other LaTeX warnings (unique, first 10) ===")
seen = []
for m in re.findall(r"LaTeX Warning: [^\n]*", log):
    if m not in seen:
        seen.append(m)
for m in seen[:10]:
    print(f"  {m[:118]}")

print()
print("=== theory.tex lines 70-100 ===")
lines = (P3 / "sections" / "theory.tex").read_text(encoding="utf-8").splitlines()
for n in range(70, 100):
    if n < len(lines):
        print(f"  {n + 1:>4} {lines[n][:108]}")
