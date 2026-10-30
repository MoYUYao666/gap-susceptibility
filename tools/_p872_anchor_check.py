# -*- coding: utf-8 -*-
r"""Check the anchors tools/_p872_fix_table_float.py needs, without shell quoting in the way.

    python tools/_p872_anchor_check.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCS = [REPO / "paper合" / "sections" / "empirical.tex",
        REPO / "paper合" / "NC_submission" / "latex_source" / "sections" / "empirical.tex"]

for p in DOCS:
    t = io.open(p, encoding="utf-8").read()
    print(p.name)
    for name, needle in (
        ("end tabular + end table", "\\end{tabular}\n\\end{table}"),
        ("end tabular", "\\end{tabular}"),
        ("end table", "\\end{table}"),
        ("caption start", "\\caption{The three adaptation positions under strict freezing"),
        ("label", "\\label{tab:position_strict}"),
        ("duplicate sentence", "Every row is a five-seed mean"),
        ("note marker", "Note on the $R@1$ column"),
    ):
        print(f"   {name:<24} {t.count(needle)}")
    i = t.find("\\end{tabular}")
    if i > 0:
        print("   context:", repr(t[i - 60:i + 40]))
