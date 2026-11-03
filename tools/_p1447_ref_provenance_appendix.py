# -*- coding: utf-8 -*-
r"""Reference the provenance appendix from the data-availability statements (clears the C-07 dead-label warning).

    python tools/_p1447_ref_provenance_appendix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    ("paper_a1/main.tex", "Data and code availability}"),
    ("paper_a2/main_ieee.tex", "Data availability}"),
    ("paper合/main_nc.tex", "Data availability}"),
    ("paper合/main_springer.tex", "Data availability}"),
]
SENT = ("The generating script and result archive of every table and figure are listed in "
        "Appendix~\\ref{app:provenance}.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for rel, anchor in TARGETS:
        p = os.path.join(REPO, rel)
        t = io.open(p, encoding="utf-8").read()
        if "listed in Appendix~\\ref{app:provenance}" in t:
            print("  already referenced:", rel)
            continue
        i = t.find(anchor)
        assert i >= 0, rel
        j = t.find("\n\n", i)
        assert j > i, rel
        t = t[:j] + " " + SENT + t[j:]
        print("  inserted ref in", rel)
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(t)
    if a.apply:
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
