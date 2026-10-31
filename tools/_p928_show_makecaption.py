# -*- coding: utf-8 -*-
r"""Print IEEEtran's `\@makecaption` as it exists at `\begin{document}`.

The patch attempt reported "caption patch failed", which means the pattern `\vskip\abovecaptionskip` is
not in the macro. This dumps the macro with `\show` so the real code can be read, then the correct patch
can be written.

    python tools/_p928_show_makecaption.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

PROBE = (B + "AtBeginDocument{" + B + "show" + B + "@makecaption}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    if PROBE in t:
        print("  probe already present")
        return 0
    anchor = B + "makeatother\n"
    assert t.count(anchor) >= 1, "no \\makeatother to anchor to"
    # insert the probe right after \begin{document}
    doc = t.find(B + "begin{document}")
    assert doc > 0
    nl = t.find("\n", doc) + 1
    probe = (B + "makeatletter\n" + B + "AtBeginDocument{" + B + "show" + B + "@makecaption}\n"
             + B + "makeatother\n")
    out = t[:nl] + probe + t[nl:]
    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")
    print("  probe inserted after \\begin{document}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
