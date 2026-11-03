# -*- coding: utf-8 -*-
r"""Fix the two gate failures found after the commentary upgrade.

1. The three new reference keys live in `paper_review_prl/_refs_used.json` but the legacy library
   `paper_review/refs_all.json` is what `_final_check_prl.py` checks. Add the same three entries there.
2. The checklist-numbering check located §4 by the first occurrence of "reporting checklist", which is in §1;
   locate the section heading instead.

    python tools/_p1349_fix_commentary_gates.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(REPO, "paper_review", "refs_all.json")
CHECK = os.path.join(REPO, "tools", "_final_check_prl.py")

NEW = [
    {"key": "sharma2026readout", "title": "One Geometry, Different Outcomes: Readout-Dependent Effects of the Modality Gap in Vision-Language Models",
     "authors": ["Aditya Sharma", "Divya Saxena"], "year": 2026, "venue": "arXiv", "doi": "",
     "arxiv_id": "2609.36101", "type": "preprint", "claim_used_for": "§3 scope: why the gap matters vs which number is comparable"},
    {"key": "yaras2026explaining", "title": "Explaining and Mitigating the Modality Gap in Contrastive Multimodal Learning",
     "authors": ["Can Yaras", "Siyi Chen", "Peng Wang", "Qing Qu"], "year": 2024, "venue": "arXiv", "doi": "",
     "arxiv_id": "2412.07909", "type": "preprint", "claim_used_for": "§3 scope: gradient-flow account of the gap"},
    {"key": "amblard2026quantifying", "title": "Quantifying and reducing the modality gap in both contrastive and generative multimodal vision-language models",
     "authors": ["François Role", "Sébastien Meyer", "Victor Amblard"], "year": 2026,
     "venue": "International Journal of Multimedia Information Retrieval", "doi": "10.1007/s13735-026-00423-w",
     "arxiv_id": "", "type": "journal", "claim_used_for": "§3 scope: quantifying and reducing the gap"},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    lib = json.load(io.open(LIB, encoding="utf-8"))
    have = {e["key"] for e in lib}
    add = [e for e in NEW if e["key"] not in have]
    print(f"  library additions: {len(add)}")
    c = io.open(CHECK, encoding="utf-8").read()
    old = '    a2 = pdfn.find("reporting checklist")'
    new = '    a2 = pdfn.find("A reporting checklist")\n    if a2 < 0:\n        a2 = pdfn.find("reporting checklist")'
    need = old in c
    print(f"  checker anchor patch needed: {need}")
    if not a.apply:
        print("  (dry run)")
        return 0
    if add:
        lib.extend(add)
        io.open(LIB, "w", encoding="utf-8", newline="").write(json.dumps(lib, ensure_ascii=False, indent=1))
        print("  library updated")
    if need:
        io.open(CHECK, "w", encoding="utf-8", newline="").write(c.replace(old, new, 1))
        print("  checker patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
