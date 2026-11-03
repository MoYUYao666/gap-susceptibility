# -*- coding: utf-8 -*-
r"""Register Abstract.pdf in the Paper A package README and in the paperA_nc audit profile.

    python tools/_p1248_register_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(REPO, "SUBMISSION", "PaperA_Neurocomputing", "README.md")
PROFILES = os.path.join(REPO, "tools", "paper_audit", "profiles.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    r = io.open(README, encoding="utf-8").read()
    print("  README has Abstract row:", "Abstract.pdf" in r)
    if "Abstract.pdf" not in r:
        row = "| Abstract | `Abstract.pdf` | 1 page; standalone abstract + keywords (Editorial Manager item) |\n"
        anchor = "| Highlights |"
        n = r.count(anchor)
        print(f"  README anchor '| Highlights |': {n}")
        if n == 0:
            print("  !! README layout unexpected")
            return 1
        r = r.replace(anchor, row + anchor, 1)

    p = io.open(PROFILES, encoding="utf-8").read()
    old_exp = ('        package_expected=["Manuscript.pdf", "Cover Letter.pdf", "Highlights.pdf",\n'
               '                          "Highlights.txt", "latex_source.zip", "README.md"],')
    new_exp = ('        package_expected=["Manuscript.pdf", "Cover Letter.pdf", "Highlights.pdf",\n'
               '                          "Highlights.txt", "Abstract.pdf", "latex_source.zip", "README.md"],')
    old_map = ('        package_map=[["Manuscript.pdf", "main_nc.pdf"],\n'
               '                     ["Cover Letter.pdf", "cover_letter_nc.pdf"],\n'
               '                     ["Highlights.pdf", "highlights_nc.pdf"],\n'
               '                     ["Highlights.txt", "highlights_nc.txt"]],')
    new_map = ('        package_map=[["Manuscript.pdf", "main_nc.pdf"],\n'
               '                     ["Cover Letter.pdf", "cover_letter_nc.pdf"],\n'
               '                     ["Highlights.pdf", "highlights_nc.pdf"],\n'
               '                     ["Highlights.txt", "highlights_nc.txt"],\n'
               '                     ["Abstract.pdf", "abstract_nc.pdf"]],')
    print(f"  profile package_expected block: {p.count(old_exp)} | package_map block: {p.count(old_map)}")
    if p.count(old_exp) == 1 and p.count(old_map) == 1:
        p = p.replace(old_exp, new_exp, 1).replace(old_map, new_map, 1)

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(README, "w", encoding="utf-8", newline="").write(r)
    io.open(PROFILES, "w", encoding="utf-8", newline="").write(p)
    print("  README + profile updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
