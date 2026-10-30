# -*- coding: utf-8 -*-
r"""Check that the numbers the main text attributes to supplement sections are actually there.

Before editing either document, confirm the claimed content exists, so the new section numbers point at
passages that真的 contain what the main text says they contain.

    python tools/_p887_p3_claim_values.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
SUPP = (P3 / "supplementary" / "supplementary.tex").read_text(encoding="utf-8", errors="replace")

CLAIMS = {
    "S3 sample-size: 16 and 256": ["16", "256"],
    "S3 sample-size: p = 0.0078": ["0.0078"],
    "S3 sample-size: 8/8": ["8/8"],
    "S5 ShareGPT bracketing": ["ShareGPT", "[5,6]"],
    "S5 ShareGPT: 45 runs": ["45"],
    "S4 rank scaling: -105, +62, +1572, +2860": ["-105", "+62", "+1572", "+2860"],
    "S4 rank scaling: 16--26x": ["26"],
    "S6 decoder VLM: 7 of 7": ["7$ of $7", "7 of 7", "7$ of"],
    "S6 decoder VLM: 15 / 54 tokens": ["15", "54"],
    "S7 downstream: 0.7241 / 0.6927": ["0.7241", "0.6927"],
    "S7 downstream: -0.374 / +0.172": ["0.374", "0.172"],
    "S7 downstream: 78 and 54 runs": ["78", "54"],
    "S7 downstream: frozen R@1 0.7058": ["0.7058"],
}
for name, needles in CLAIMS.items():
    hits = {n: SUPP.count(n) for n in needles}
    ok = all(v > 0 for v in hits.values())
    print(f"  {'OK ' if ok else 'MISS'} {name:<44} {hits}")

print()
print("=== main text values attributed to the supplement ===")
main = (P3 / "main.tex").read_text(encoding="utf-8", errors="replace")
for p in sorted((P3 / "sections").glob("*.tex")):
    if ".bak" not in p.name:
        main += "\n" + p.read_text(encoding="utf-8", errors="replace")
for val in ("0.7241", "0.6927", "0.7058", "0.374", "0.172", "0.0078"):
    print(f"  main says {val}: {main.count(val)}  | supplement has it: {SUPP.count(val)}")

print()
print("=== does the supplement have a table for the sample-size sweep? ===")
print(f"  tables in supplement: {len(re.findall(r'begin.table', SUPP))}")
for m in re.finditer(r"\\caption\{([^}]{0,70})", SUPP):
    print(f"    {m.group(1)}")
