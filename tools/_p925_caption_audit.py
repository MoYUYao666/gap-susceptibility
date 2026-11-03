# -*- coding: utf-8 -*-
r"""Report where each supplement caption sits relative to its table body, and the caption settings.

The caption-to-rule gap came out at 8.8 mm for Table S3 but only 3.4 mm for Table S5, so the setting is
not reaching every table. This prints the caption package state and each table's caption position (before
or after the tabular), which is what decides which skip applies.

    python tools/_p925_caption_audit.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
LOG = SUPP.parent / "supplementary.log"
B = chr(92)

t = SUPP.read_text(encoding="utf-8")
print("=== caption settings in the source ===")
for m in re.finditer(re.escape(B) + r"captionsetup[^\n]*", t):
    print(f"  line {t[:m.start()].count(chr(10)) + 1}: {m.group(0)}")
print(f"  \\usepackage{{caption}} present: {B + 'usepackage{caption}' in t}")

print()
print("=== caption position per table ===")
for m in re.finditer(re.escape(B) + r"begin\{table\*?\}", t):
    start = m.start()
    ln = t[:start].count("\n") + 1
    end = t.find(B + "end{table", start)
    block = t[start:end]
    lab = re.search(re.escape(B) + r"label\{([^}]*)\}", block)
    cap_at = block.find(B + "caption")
    tab_at = block.find(B + "begin{tabular}")
    where = "before the tabular" if cap_at < tab_at else "after the tabular"
    print(f"  line {ln:<5} {(lab.group(1) if lab else '-'):<18} caption is {where}")

print()
print("=== what the log says about caption ===")
log = LOG.read_text(encoding="utf-8", errors="replace")
for pat in (r"Package: caption[^\n]*", r"caption[^\n]*Warning[^\n]*"):
    for m in re.findall(pat, log)[:4]:
        print(f"  {m[:110]}")
