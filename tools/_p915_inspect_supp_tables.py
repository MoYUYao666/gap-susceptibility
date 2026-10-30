# -*- coding: utf-8 -*-
r"""Show the supplement's table environments, their column specs and their captions.

Reported fault: the text in Table S3 is squeezed. This prints what each table is built from, so the
column specification and the caption width can be checked against what the page actually allows.

    python tools/_p915_inspect_supp_tables.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

t = SUPP.read_text(encoding="utf-8")
print(f"=== {SUPP.name}: {len(t.splitlines())} lines ===")
for m in re.finditer(re.escape(B) + r"begin\{table\*?\}", t):
    ln = t[: m.start()].count("\n") + 1
    end = t.find(B + "end{table", m.end())
    block = t[m.start(): end + 14]
    lab = re.search(re.escape(B) + r"label\{([^}]*)\}", block)
    spec = re.search(re.escape(B) + r"begin\{tabular\}\{([^}]*)\}", block)
    cap = re.search(re.escape(B) + r"caption\{(.*?)\}" + re.escape(B) + r"label", block, re.S)
    cap_txt = re.sub(r"\s+", " ", cap.group(1)).strip() if cap else "(none)"
    size = re.search(re.escape(B) + r"(footnotesize|small|scriptsize|tiny)", block)
    cols = spec.group(1) if spec else "?"
    print()
    print(f"  line {ln}: {m.group(0)}  label={lab.group(1) if lab else None}  "
          f"font={size.group(1) if size else 'default'}")
    print(f"    column spec: {cols}")
    print(f"    caption ({len(cap_txt)} chars): {cap_txt[:150]}")
    for row in re.findall(r"^.*?" + re.escape(B * 2) + r"$", block, re.M)[:12]:
        print(f"      row: {re.sub(chr(92) + 's+', ' ', row.strip())[:120]}")
