# -*- coding: utf-8 -*-
r"""Commentary: add a compact six-instance table and trim prose so the 7-page limit still holds.

    python tools/_p1359_commentary_table.py [--apply]
"""
from __future__ import annotations

import argparse
import io

MD = "paper_review_prl/MANUSCRIPT.md"

TABLE = """**Table 3.** The six instances of §3 in one view.

| Instance | What is usually reported | Item that would make it comparable |
|---|---|---|
| Same model, same benchmark | a single accuracy, evaluation subset unnamed | state the benchmark subset and version |
| Protocol change | vanilla and circular scores placed side by side | report the evaluation protocol |
| Parameter count as budget | a trainable-parameter total | state the budget composition |
| Failure values | NaN or 0 without semantics | define failure semantics |
| Variance | a spread under an unstated convention | state the variance convention |
| Freeze as baseline | a frozen model treated as a neutral anchor | report the initialisation and freeze regime |
"""

TRIMS = [
    # section 3.7 opening: keep the three conclusions, drop the explanatory tail of the first one
    (' First, *site dominates allocation in the small-data regime*: with a small task corpus, which\n'
     'site is trainable matters more than how a budget is divided within it, because a small corpus gives\n'
     'little signal with which to estimate an importance score [zhang2023adalora; wang2024loraga; zanella2024cliplora].',
     ' First, *site dominates allocation in the small-data regime*: with a small task corpus, which site is\n'
     'trainable matters more than how the budget is divided within it [zhang2023adalora; wang2024loraga;\n'
     'zanella2024cliplora].'),
    # section 2.3 third paragraph: keep the point, drop the repetition
    ('Third, separation is what makes comparison possible at all. If two papers differ in both decisions,\n'
     'their numbers can differ for either reason, and no amount of careful reading will attribute the\n'
     'difference.',
     'Third, separation is what makes comparison possible: if two papers differ in both decisions, their\n'
     'numbers can differ for either reason, and no amount of careful reading will attribute the difference.'),
    # conclusions, second paragraph: compress the list
    ('The instances are not allegations of error. In each case the information needed for comparison is\n'
     'absent rather than wrong: an evaluation subset unnamed, a protocol unstated, a distribution\n'
     'undescribed, a failure recorded without its cause, dispersion reported without its convention, and a\n'
     'frozen component described without saying which parts moved. The checklist in §4 is the minimum that\n'
     'removes these obstacles.',
     'The instances are not allegations of error: in each case the information needed for comparison is\n'
     'absent rather than wrong, and the checklist in §4 is the minimum that removes these obstacles.'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MD, encoding="utf-8").read()
    changed = 0
    for old, new in TRIMS:
        if old in t:
            t = t.replace(old, new, 1)
            changed += 1
        else:
            print("  missing trim:", old[:60])
    if "**Table 3.** The six instances of §3 in one view." not in t:
        anchor = "### 3.7 What a practitioner can still conclude"
        assert t.count(anchor) == 1
        t = t.replace(anchor, TABLE + "\n" + anchor, 1)
        changed += 1
    print(f"  changes: {changed}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MD, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
