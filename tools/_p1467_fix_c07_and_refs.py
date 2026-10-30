# -*- coding: utf-8 -*-
r"""Fix the two C-07 dead appendix labels and register the new Commentary reference in the global library.

    python tools/_p1467_fix_c07_and_refs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A1 = os.path.join(REPO, "paper_a1", "main.tex")
EMP = os.path.join(REPO, "paper合", "sections", "empirical.tex")
REFS_ALL = os.path.join(REPO, "paper_review", "refs_all.json")
REF = {"key": "sun2026reading",
       "authors": "Kaiser Sun, Xiaochuang Yuan, Hongjun Liu, Chen Zhao, Cheng Zhang, Mark Dredze, Fan Bai",
       "title": "Reading, Not Thinking: Understanding and Bridging the Modality Gap When Text Becomes Pixels in "
                "Multimodal LLMs",
       "year": 2026, "venue": "arXiv", "arxiv": "2603.09095", "doi": "10.48550/arXiv.2603.09095"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    changed = False
    t = io.open(A1, encoding="utf-8").read()
    old = " Appendix Table~\\ref{tab:monitor_variants} collects the rule variants across the three task types."
    new = (" Appendix~\\ref{app:monitor_variants} collects the rule variants across the three task types "
           "(Table~\\ref{tab:monitor_variants}).")
    if old in t:
        t = t.replace(old, new, 1)
        io.open(A1, "w", encoding="utf-8", newline="").write(t)
        changed = True
        print("  A1 pointer updated")
    e = io.open(EMP, encoding="utf-8").read()
    old2 = " (per-family and per-site residual structure in Appendix Table~\\ref{tab:odefit})."
    new2 = (" (per-family and per-site residual structure in Appendix~\\ref{app:odefit}, "
            "Table~\\ref{tab:odefit}).")
    if old2 in e:
        e = e.replace(old2, new2, 1)
        io.open(EMP, "w", encoding="utf-8", newline="").write(e)
        changed = True
        print("  Paper A pointer updated")
    if os.path.exists(REFS_ALL):
        d = json.load(io.open(REFS_ALL, encoding="utf-8"))
        if not any(r.get("key") == "sun2026reading" for r in d):
            d.append(REF)
            io.open(REFS_ALL, "w", encoding="utf-8", newline="").write(json.dumps(d, indent=1, ensure_ascii=False))
            changed = True
            print("  refs_all updated")
    if a.apply and changed:
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
