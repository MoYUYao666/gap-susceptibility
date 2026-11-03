# -*- coding: utf-8 -*-
r"""Inventory P3's supplementary material: sections, tables, figures, and broken cross-references.

The earlier pass over this file used regexes that ended up matching nothing, which is why the problem
was missed: several cross-references in the supplement had their numbers replaced by the words "the
main text" or the object's own name, so they point nowhere.

    python tools/_p882_p3_supp_inventory.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
SUPP = P3 / "supplementary" / "supplementary.tex"
MAIN_SRC = [P3 / "main.tex"] + [p for p in (P3 / "sections").glob("*.tex") if ".bak" not in p.name]


def inventory(path: Path, label: str) -> None:
    t = path.read_text(encoding="utf-8", errors="replace")
    print(f"=== {label} ({path.name}) ===")
    secs = re.findall(r"\\section\{([^}]*)\}", t)
    print(f"  numbered sections: {len(secs)}")
    for i, s in enumerate(secs, 1):
        print(f"    S{i}: {s}")
    subs = re.findall(r"\\subsection\{([^}]*)\}", t)
    print(f"  subsections: {len(subs)}")
    tabs = re.findall(r"\\begin\{table\*?\}", t)
    figs = re.findall(r"\\begin\{figure\*?\}", t)
    labels = re.findall(r"\\label\{([^}]*)\}", t)
    print(f"  tables: {len(tabs)}  figures: {len(figs)}  labels: {len(labels)} {labels}")
    print("  broken cross-references (number replaced by text):")
    for pat in (r"Theorem~[A-Za-z]\w*", r"Lemma~[A-Za-z]\w*", r"Section~[A-Za-z]\w*",
                r"Table~[A-Za-z]\w*", r"Figure~[A-Za-z]\w*", r"Equation~[A-Za-z]\w*"):
        for m in re.finditer(pat, t):
            ln = t[: m.start()].count("\n") + 1
            print(f"    line {ln:>4}: {m.group(0)}")
    # references to supplement objects by their printed number
    for pat in (r"Table~S\d+", r"Figure~S\d+", r"Section~S\d+", r"Supplementary (?:Table|Figure|Section)~?S?\d*"):
        hits = re.findall(pat, t)
        if hits:
            print(f"  refs by printed number {pat}: {sorted(set(hits))}")


inventory(SUPP, "SUPPLEMENT")
print()
for p in MAIN_SRC:
    inventory(p, "MAIN")
