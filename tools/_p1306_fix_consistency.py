# -*- coding: utf-8 -*-
r"""Fix three consistency defects found by the cross-check.

1. `_p1236` wrote "2 pages" for the cover letter into the package README (the letter is one page); make it measured.
2. `_p1284` (public-mirror staging list) did not include the four newest archives and their scripts.
3. `AUTOMATION_HANDOVER.md` still said the A1 package was 51 pages without the claim ledger.

    python tools/_p1306_fix_consistency.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(REPO, "tools", "_p1236_build_paa_package.py")
MIRROR = os.path.join(REPO, "tools", "_p1284_prepare_public_mirror.py")
AUTO = os.path.join(REPO, "AUTOMATION_HANDOVER.md")

NEW_FILES = '''    "outputs/analysis/a1_matched_gap_dense.json",
    "outputs/analysis/a1_real_checkpoint_pairs.json",
    "outputs/analysis/a1_lower_bound_constants.json",
    "outputs/analysis/a1_margin_mass.json",
    "tools/_p1299_margin_mass.py",
    "tools/_p1300_matched_gap_dense.py",
    "tools/_p1301_lower_bound_constants.py",
    "tools/_p1302_insert_novelty_b.py",
'''

AUTO_OLD = ("包在 `SUBMISSION/A1_PatternAnalysisApplications/`（**51 页** + 1 页 title page + 揭示函），"
            "审计 `a1_paa` READY/A，**待投**。")
AUTO_NEW = ("包在 `SUBMISSION/A1_PatternAnalysisApplications/`（**54 页** + 1 页 title page + 揭示函 + 图摘要），"
            "**A1 claim ledger 112/112**，审计 `a1_paa` READY/A，**待投**。")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    b = io.open(BUILD, encoding="utf-8").read()
    old_row = "| Cover Letter | `Cover Letter.pdf` | 2 pages; discloses prior submission history and related work |"
    new_row = "| Cover Letter | `Cover Letter.pdf` | %d page; discloses prior submission history and related work |"
    n = b.count(old_row)
    print(f"  build README cover row: {n}")
    assert n == 1
    b = b.replace(old_row, new_row, 1)
    old_args = "% (pages(os.path.join(A1, \"main.pdf\")), 239)"
    new_args = "%% (pages(os.path.join(A1, \"main.pdf\")), pages(os.path.join(A1, \"cover_letter_paa.pdf\")), 239)"
    print(f"  build README args: {b.count(old_args)}")
    assert b.count(old_args) == 1
    b = b.replace(old_args, new_args, 1)
    # the row now needs a third argument position: move the compliance sentence's %d to stay after the page args
    b = b.replace("Compliance (Pattern Analysis and Applications guide, read 2026-10-18): abstract %d words",
                  "Compliance (Pattern Analysis and Applications guide, read 2026-10-18): abstract %d words", 1)
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(BUILD, "w", encoding="utf-8", newline="").write(b)
    print("  builder README patched")

    m = io.open(MIRROR, encoding="utf-8").read()
    if "a1_matched_gap_dense.json" not in m:
        anchor = '    "outputs/analysis/claim_ledger_a1.json",'
        assert m.count(anchor) == 1
        m = m.replace(anchor, anchor + "\n" + NEW_FILES.rstrip("\n"), 1)
        io.open(MIRROR, "w", encoding="utf-8", newline="").write(m)
        print("  mirror staging list extended")
    else:
        print("  mirror staging list already complete")

    au = io.open(AUTO, encoding="utf-8").read()
    n = au.count(AUTO_OLD)
    print(f"  automation 51-page line: {n}")
    if n == 1:
        io.open(AUTO, "w", encoding="utf-8", newline="").write(au.replace(AUTO_OLD, AUTO_NEW, 1))
        print("  automation handover updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
