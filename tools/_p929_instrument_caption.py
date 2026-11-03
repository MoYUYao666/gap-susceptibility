# -*- coding: utf-8 -*-
r"""Instrument the table-caption separator so the value it uses is visible in the log.

`\@makecaption` does call `\@IEEEtablecaptionsepspace` for tables, so the gap should follow
`\abovecaptionskip`. It does not, which means either the macro is not being called or something later
redefines it. This makes the macro print its value and its invocation count.

    python tools/_p929_instrument_caption.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

PATCH = (B + "newcount" + B + "pthreecaptioncount\n"
         + B + "AtBeginDocument{%\n"
         + "  " + B + "setlength{" + B + "abovecaptionskip}{22pt}%\n"
         + "  " + B + "def" + B + "@IEEEtablecaptionsepspace{%\n"
         + "    " + B + "advance" + B + "pthreecaptioncount by 1 %\n"
         + "    " + B + "typeout{P3: table caption separator fired #" + B + "the" + B + "pthreecaptioncount,"
         + " abovecaptionskip=" + B + "the" + B + "abovecaptionskip}%\n"
         + "    " + B + "vskip" + B + "abovecaptionskip" + B + "relax}%\n"
         + "}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    if B + "pthreecaptioncount" in t:
        print("  already instrumented")
        return 0
    # remove the probe inserted by _p928
    probe = B + "makeatletter\n" + B + "AtBeginDocument{" + B + "show" + B + "@makecaption}\n" + B + "makeatother\n"
    if probe in t:
        t = t.replace(probe, "", 1)
        print("  removed the \\show probe")
    # the failed patchcmd line, if present, is replaced by the instrumentation
    import re
    t = re.sub(re.escape(B) + r"patchcmd\{" + re.escape(B) + r"@makecaption\}.*?\n", "", t, flags=re.S)
    anchor = B + "makeatother\n"
    assert anchor in t, "no \\makeatother anchor"
    out = t.replace(anchor, anchor + PATCH, 1)
    print("  instrumented \\@IEEEtablecaptionsepspace and set \\abovecaptionskip to 22pt")
    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
