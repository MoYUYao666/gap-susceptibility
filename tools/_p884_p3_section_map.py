# -*- coding: utf-8 -*-
r"""Map each supplementary section to the content it holds, and check every cross-reference in both P3
documents against what actually exists.

    python tools/_p884_p3_section_map.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
SUPP = P3 / "supplementary" / "supplementary.tex"

t = SUPP.read_text(encoding="utf-8", errors="replace")
marks = [(m.start(), m.group(1)) for m in re.finditer(r"\\section\{([^}]*)\}", t)]
print(f"numbered sections: {len(marks)}")
for i, (pos, name) in enumerate(marks):
    end = marks[i + 1][0] if i + 1 < len(marks) else len(t)
    body = t[pos:end]
    subs = re.findall(r"\\subsection\{([^}]*)\}", body)
    tabs = len(re.findall(r"\\begin\{table", body))
    figs = len(re.findall(r"\\begin\{figure", body))
    labs = re.findall(r"\\label\{([^}]*)\}", body)
    print(f"  S{i + 1}: {name[:52]:<54} subs={len(subs)} tab={tabs} fig={figs} labels={labs}")
    for s in subs:
        print(f"        - {s[:72]}")

print()
print("=== every cross-reference in the supplement, and whether its target exists ===")
table_labels = [m.group(1) for m in re.finditer(r"\\label\{(tab:[^}]*)\}", t)]
figure_labels = [m.group(1) for m in re.finditer(r"\\label\{(fig:[^}]*)\}", t)]
print(f"  supplement tables: {table_labels}")
print(f"  supplement figures: {figure_labels}")
n_sec = len(marks)
for m in re.finditer(r"(?:Supplementary\s+)?(Section|Table|Figure|Theorem|Lemma|Corollary)~?"
                     r"(?:Supplementary\s+)?(?:Table|Figure|Section)?~?\s*([A-Z]?[IVX0-9]+[A-Za-z-]*)", t):
    ln = t[: m.start()].count("\n") + 1
    kind, num = m.group(1), m.group(2)
    print(f"  line {ln:>4}: {kind} {num}")

print()
print("=== the same, in the main text ===")
main = (P3 / "main.tex").read_text(encoding="utf-8", errors="replace")
for p in sorted((P3 / "sections").glob("*.tex")):
    if ".bak" not in p.name:
        main += "\n" + p.read_text(encoding="utf-8", errors="replace")
for m in re.finditer(r"Supplementary\s+(Section|Table|Figure)s?~?([A-Z]?[0-9S]*)", main):
    ln = main[: m.start()].count("\n") + 1
    print(f"  line {ln:>4}: {m.group(0)}")
