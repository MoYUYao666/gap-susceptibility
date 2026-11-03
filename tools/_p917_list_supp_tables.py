# -*- coding: utf-8 -*-
r"""List the supplement's tables with their column spec and font command.

    python tools/_p917_list_supp_tables.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

t = SUPP.read_text(encoding="utf-8")
for m in re.finditer(re.escape(B) + r"begin\{table\*?\}", t):
    ln = t[: m.start()].count("\n") + 1
    seg = t[m.start(): m.start() + 1200]
    lab = re.search(re.escape(B) + r"label\{([^}]*)\}", seg)
    spec = re.search(re.escape(B) + r"begin\{tabular\}\{([^}]*)\}", seg)
    fs = re.search(r"(footnotesize|fontsize\{[^}]*\})", seg)
    print(f"  line {ln:<5} label={(lab.group(1) if lab else '-'):<18} "
          f"spec={(spec.group(1) if spec else '-'):<12} font={fs.group(1) if fs else 'default'}")
