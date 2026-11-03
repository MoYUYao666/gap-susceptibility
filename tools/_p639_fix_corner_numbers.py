# -*- coding: utf-8 -*-
r"""Replace the superseded 3-seed corner/interior numbers with the current 6-seed ones.

The paper's Section IV-E (and the matching sentences in theory.tex and the frozen
sections_full/ copies) compare the linear-surrogate corner with the Gamma-guided interior
solution using values from the 3-seed era:

    corner            +3607 +- 514      -> superseded
    interior (exp)    +2241 +- 1291     -> superseded

The archive now holds 6 seeds per arm. Recomputed from the per-run records under
outputs/analysis/p3_alloc_runs/main/:

    exp_beta_paper_0.137   n=6  mean +1477.45  sd 1563.34
    corner                 n=6  mean +2343.90  sd 2426.09
    uniform                n=6  mean +5047.55  sd 1899.90

The same paragraph already quotes the 6-seed values for the other two arms (+1478, +5048),
so the current text mixes two generations of data in one sentence. This makes it consistent.

    python tools/_p639_fix_corner_numbers.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper3" / "paper_ieee"
SRC_COPY = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / "latex_source"

OLD_CORNER = r"+3607 \pm 514"
NEW_CORNER = r"+2344 \pm 2426"
OLD_INTERIOR = r"+2241 \pm 1291"
NEW_INTERIOR = r"+1477 \pm 1563"
OLD_CORNER_T = r"\Delta E=+3607\pm514"
NEW_CORNER_T = r"\Delta E=+2344\pm2426"
OLD_INTERIOR_T = r"+2241\pm1291"
NEW_INTERIOR_T = r"+1477\pm1563"

TARGETS = [
    PAPER / "sections" / "experiments.tex",
    PAPER / "sections" / "theory.tex",
    PAPER / "sections_full" / "experiments.tex",
    PAPER / "sections_full" / "theory.tex",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    plan = []
    for p in TARGETS:
        if not p.exists():
            print(f"  MISSING {p.relative_to(REPO)}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n1, n2 = t.count(OLD_CORNER), t.count(OLD_INTERIOR)
        m1, m2 = t.count(OLD_CORNER_T), t.count(OLD_INTERIOR_T)
        # the theory.tex variant has no spaces
        t2 = t.replace(OLD_CORNER, NEW_CORNER).replace(OLD_INTERIOR, NEW_INTERIOR)
        t2 = t2.replace(OLD_CORNER_T, NEW_CORNER_T).replace(OLD_INTERIOR_T, NEW_INTERIOR_T)
        # also the odd "corner scores \Delta E = +3607 \pm 514" in sections_full/theory
        changed = (n1 + n2 + m1 + m2)
        total += changed
        print(f"  {p.relative_to(REPO)}")
        print(f"     '+3607 \\pm 514' x{n1}   '+2241 \\pm 1291' x{n2}   "
              f"no-space variants x{m1 + m2}")
        plan.append((p, t, t2, changed))
    print()
    print(f"  total replacements: {total}")
    if not total:
        print("  nothing to do")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0
    for p, t, t2, changed in plan:
        if not changed:
            continue
        bak = p.with_suffix(p.suffix + ".bak_p639")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
    # refresh the source-package copy of the changed sections
    for rel in ("sections/experiments.tex", "sections/theory.tex"):
        src = PAPER / rel
        dst = SRC_COPY / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  synced {rel} into the source package")
    print()
    print("  Re-check (stale values must be gone):")
    for p in TARGETS + [SRC_COPY / "sections" / "experiments.tex",
                        SRC_COPY / "sections" / "theory.tex"]:
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        bad = t.count("3607") + t.count("2241")
        ok = t.count("2344") + t.count("1477")
        print(f"    {p.relative_to(REPO):<58} stale={bad}  current={ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
