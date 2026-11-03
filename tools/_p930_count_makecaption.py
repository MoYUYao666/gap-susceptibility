# -*- coding: utf-8 -*-
r"""Count how often `\@makecaption` runs, to see whether IEEEtran's version is the one in use.

The table separator macro never fired, so either the captions do not go through IEEEtran's
`\@makecaption` at all, or `\@captype` is not what the class expects. Counting invocations separates
those two cases.

    python tools/_p930_count_makecaption.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

WRAPPER = (B + "newcount" + B + "pthreecapcount\n"
           + B + "AtBeginDocument{%\n"
           + "  " + B + "let" + B + "pthreeorigmakecaption" + B + "@makecaption\n"
           + "  " + B + "long" + B + "def" + B + "@makecaption#1#2{%\n"
           + "    " + B + "advance" + B + "pthreecapcount by 1 %\n"
           + "    " + B + "typeout{P3: makecaption #" + B + "the" + B + "pthreecapcount,"
           + " captype=" + B + "meaning" + B + "@captype,"
           + " abovecaptionskip=" + B + "the" + B + "abovecaptionskip}%\n"
           + "    " + B + "vskip 22pt" + B + "relax\n"
           + "    " + B + "pthreeorigmakecaption{#1}{#2}}%\n"
           + "}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    if B + "pthreecapcount" in t:
        print("  already instrumented")
        return 0
    # drop the previous instrumentation
    import re
    t = re.sub(re.escape(B) + r"newcount" + re.escape(B) + r"pthreecaptioncount.*?\n\}\n", "", t, flags=re.S)
    anchor = B + "makeatother\n"
    assert anchor in t, "no \\makeatother anchor"
    out = t.replace(anchor, anchor + WRAPPER, 1)
    print("  wrapper installed: it counts captions, logs the float type, and adds 22 pt before the caption")
    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
