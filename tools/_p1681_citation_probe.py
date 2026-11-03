"""Debug: how do citations render in the Applied Intelligence (sn-jnl/sn-basic) build?

Read-only. Prints the number of \\cite commands in the reframed sections, the \\bibpunct the class
sets, and the rendered text around the first few citation sites in Manuscript.pdf.

Usage: python tools/_p1681_citation_probe.py
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    total = 0
    per = {}
    for f in sorted((REPO / "paper合" / "reframed" / "sections").glob("*.tex")):
        t = io.open(f, encoding="utf-8").read()
        n = len(re.findall(r"\\cite\{", t))
        per[f.name] = n
        total += n
    print("\\cite in reframed sections:", total)
    for k, v in per.items():
        if v:
            print("   %-28s %d" % (k, v))

    cls = io.open(REPO / "paper合" / "sn-jnl.cls", encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"\\bibpunct[^\n]{0,160}", cls):
        print("class bibpunct:", m.group(0)[:170])

    from pypdf import PdfReader
    pdf = REPO / "SUBMISSION" / "PaperA_AppliedIntelligence" / "Manuscript.pdf"
    text = " ".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)
    norm = re.sub(r"\s+", " ", text)
    for needle in ("Methods like LoRA", "LoRA has become", "Hu et al", "Fig. 1", "Figure 1",
                   "(1)", "References", "Albert, P."):
        i = norm.find(needle)
        print("\n%-18r at %s" % (needle, i))
        if i >= 0:
            print("   ...", norm[max(0, i - 60): i + 160])
    print("\nbracket groups:", re.findall(r"\[[0-9, \-]{1,24}\]", norm)[:12])
    print("[n] count:", len(re.findall(r"\[\d+\]", norm)))
    # superscript-like digits right after a word
    print("superscript-ish:", re.findall(r"[A-Za-z]\d{1,2}(?=[\s,.;])", norm)[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
