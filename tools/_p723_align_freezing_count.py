# -*- coding: utf-8 -*-
r"""Align Paper A's strict-freezing count with the appendix table: 95 -> 104 where the table applies.

Decision (evidence in the ledger, tools/_p722):
  - the appendix table's 13 mechanism rows sum to 117
  - its XIV row is 104, and 117 + 104 = 221 = the table's own Total row
  - HANDOFF L10175/L10193 record the correction 95 -> 104 after the BioCLIP runs were added and
    note the measured value is 104
  So 104 is the count consistent with the table; the 95s in the prose are stale.

Changed: sections/supplement.tex (prose) and sections/conclusion.tex.
NOT changed: sections/empirical.tex line 4, which reads "117 under the earlier convention and 95
under strict freezing" - that is a contrast between two conventions, not a statement of the
control count, so it needs the author's judgement rather than an edit.

    python tools/_p723_align_freezing_count.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"

EDITS = [
    ("sections/supplement.tex",
     "the 117 mechanism experiments of Part~I together with the 95 strict-freezing controls",
     "the 117 mechanism experiments of Part~I together with the 104 strict-freezing controls"),
    ("sections/conclusion.tex",
     "covering 117 mechanism experiments and 95 strict-freezing controls",
     "covering 117 mechanism experiments and 104 strict-freezing controls"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for rel, old, new in EDITS:
        p = PA / rel
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {rel:<32} matches={n}")
        if n == 1 and a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p723")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            print("     rewritten")
    if not a.apply:
        print("  (dry run)")
        return 0
    print()
    print("  re-check every mention of the control count:")
    for rel in ("sections/supplement.tex", "sections/conclusion.tex",
                "sections/empirical.tex", "main_nc.tex"):
        t = io.open(PA / rel, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"(\d+)\s+strict-freezing controls", t):
            ln = t[:m.start()].count("\n") + 1
            print(f"     {rel}:{ln}  ->  {m.group(1)}")
        for m in re.finditer(r"together with the (\d+) strict", t):
            pass
    print()
    print("  the empirical.tex sentence (deliberately untouched):")
    t = io.open(PA / "sections" / "empirical.tex", encoding="utf-8", errors="replace").read()
    m = re.search(r"These experiments[^.]*\.", t)
    if m:
        print("     " + " ".join(m.group(0).split())[:260])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
