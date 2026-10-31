# -*- coding: utf-8 -*-
r"""Print the exact main-text references to supplement sections, and the supplement passages they name.

    python tools/_p886_p3_ref_contexts.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"

main = (P3 / "main.tex").read_text(encoding="utf-8", errors="replace")
for p in sorted((P3 / "sections").glob("*.tex")):
    if ".bak" not in p.name:
        main += "\n" + p.read_text(encoding="utf-8", errors="replace")

print("=== main text: every supplement cross-reference, in context ===")
for m in re.finditer(r"Supplementary\s+(?:Section|Sections|Table|Figure)s?~?[^.)\n]*", main):
    ln = main[: m.start()].count("\n") + 1
    start = main.rfind("\\noindent", 0, m.start())
    if start < 0:
        start = max(0, m.start() - 400)
    end = main.find("\n\n", m.end())
    seg = main[start:end if end > 0 else m.end() + 200].replace("\n", " ")
    print(f"--- line {ln}: {m.group(0)}")
    print(f"    {seg[:520]}")
    print()

print("=== supplement: the passages the main text names ===")
supp = (P3 / "supplementary" / "supplementary.tex").read_text(encoding="utf-8", errors="replace")
for needle in ("Sample Size Robustness", "Rank Scaling", "Second-Dataset Validation", "Decoder VLM",
               "Downstream check", "Comparison with Prior Work", "Operating-point probe"):
    for m in re.finditer(r"\\subsection\{" + re.escape(needle), supp):
        ln = supp[: m.start()].count("\n") + 1
        end = supp.find("\n\\subsection{", m.end())
        if end < 0:
            end = supp.find("\n\\section{", m.end())
        seg = supp[m.start():end if end > 0 else m.end() + 1500]
        print(f"--- {needle} (line {ln}, {len(seg.splitlines())} lines)")
        print("    " + seg[:700].replace("\n", " ")[:700])
        print()
