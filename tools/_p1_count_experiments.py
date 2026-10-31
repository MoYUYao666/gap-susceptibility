# -*- coding: utf-8 -*-
"""Count the experiment catalog: claimed per-section totals vs actual data rows."""
import io
import re
import os

ROOT = r"D:\Realdesktop\Wan\Important\New"
PATHS = ["paper/sections/supplementary.tex", "paper/sections/experiments.tex"]

for rel in PATHS:
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    lines = io.open(path, encoding="utf-8").read().split("\n")
    print("=" * 72)
    print(rel)
    print("=" * 72)
    section, rows_in_section = None, 0
    claimed_sum, sections = 0, []
    for i, ln in enumerate(lines, 1):
        m = re.search(r"\\textbf\{([IVX]+)\.\s*(.*?)\s*---\s*(\d+)\s*experiment", ln)
        if m:
            if section is not None:
                sections.append((section, claimed, rows_in_section))
                claimed_sum += claimed
            section, claimed, rows_in_section = m.group(2), int(m.group(3)), 0
            continue
        s = ln.strip()
        if not s or s.startswith("\\") and not s.startswith("\\multicolumn"):
            continue
        if s.startswith("%") or s.startswith("\\midrule") or s.startswith("\\toprule") \
           or s.startswith("\\bottomrule") or s.startswith("\\caption") \
           or s.startswith("\\label") or s.startswith("\\end") or s.startswith("\\begin"):
            continue
        if s.startswith("\\multicolumn"):
            continue
        if "&" in s and "Total" not in s and "Method" not in s and "Experiment" not in s:
            rows_in_section += 1
    if section is not None:
        sections.append((section, claimed, rows_in_section))
        claimed_sum += claimed

    total_rows = 0
    for name, claimed, actual in sections:
        flag = "" if claimed == actual else "   <-- MISMATCH"
        print("  %-46s claimed %3d  rows %3d%s" % (name[:46], claimed, actual, flag))
        total_rows += actual
    print("  %-46s claimed %3d  rows %3d"
          % ("SUM", claimed_sum, total_rows))
    # the hard-coded totals
    for i, ln in enumerate(lines, 1):
        if re.search(r"\\textbf\{116\}", ln) or "116 experiments" in ln:
            print("  [%d] hard-coded: %s" % (i, ln.strip()[:110]))
