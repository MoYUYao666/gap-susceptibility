# -*- coding: utf-8 -*-
r"""Make the table-caption gap actually change, by patching `\@makecaption` itself.

`\setlength{\abovecaptionskip}{...}` and even a redefined `\@IEEEtablecaptionsepspace` had no effect on
the rendered gap (tested with 60 pt: unchanged), so the caption path in use does not go through that
hook. This patches the two `\vskip`s inside IEEEtran's `\@makecaption` directly with `etoolbox`, which
works regardless of which macro the class happens to call, and prints a line so the log shows the value
that was applied.

    python tools/_p927_caption_sepspace.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

OLD_BLOCK_START = B + "AtBeginDocument{%\n"
GAP_PT = "22pt"

NEW = (B + "usepackage{etoolbox}\n"
       + B + "makeatletter\n"
       + B + "patchcmd{" + B + "@makecaption}{" + B + "vskip" + B + "abovecaptionskip}{"
       + B + "vskip " + GAP_PT + "}{" + B + "typeout{P3: table caption gap set to " + GAP_PT + "}}"
       + "{" + B + "typeout{P3: WARNING caption patch failed}}\n"
       + B + "makeatother\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    if B + "patchcmd{" + B + "@makecaption}" in t:
        print("  already patched")
        return 0

    start = t.find(OLD_BLOCK_START)
    assert start >= 0, "the AtBeginDocument block is not present"
    end = t.find("\n}\n", start)
    assert end > start, "the AtBeginDocument block is not terminated as expected"
    old_block = t[start: end + 3]
    assert B + "abovecaptionskip" in old_block

    out = t.replace(old_block, NEW, 1)
    print("  replaced the ineffective AtBeginDocument block with a direct \\@makecaption patch")
    print(f"  table caption gap target: {GAP_PT} (was 0.75 baselineskip = 9 pt, about 2.7 mm)")

    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")
    check = SUPP.read_text(encoding="utf-8")
    assert B + "patchcmd{" + B + "@makecaption}" in check
    assert B + "AtBeginDocument{%" not in check
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
