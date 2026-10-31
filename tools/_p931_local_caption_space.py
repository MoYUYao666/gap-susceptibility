# -*- coding: utf-8 -*-
r"""Give each supplement table space above its caption, with a local `\vspace` instead of class surgery.

Tried and rejected, in order:

* `\setlength{\abovecaptionskip}{20pt}` in the preamble -- no effect, because IEEEtran copies the length
  into its own macro while the class is read;
* redefining `\@IEEEtablecaptionsepspace` -- the macro never fired, so the caption does not go through it;
* `\captionsetup{skip=...}` from the `caption` package -- it did move the caption, but the package
  replaces IEEEtran's caption layout (the class warns "Unknown document class") and the result differed
  between tables;
* `\patchcmd` on `\@makecaption` -- reported failure, the pattern is not in the macro;
* wrapping `\@makecaption` -- "Illegal parameter number", because the class's macro is not a two-argument
  long macro in the form assumed.

What works without touching the class: one `\vspace` at the end of the float body, immediately before the
caption. It is local to the five tables in this document, cannot disturb any other caption, and its value
can be read straight off the rendered page.

    python tools/_p931_local_caption_space.py [--apply]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)
SPACE = B + "vspace{6pt}   % air between the table and its caption\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    if SPACE in t:
        print("  local caption space already present")
        return 0

    # remove the failed instrumentation and the ineffective preamble attempts
    t = re.sub(re.escape(B) + r"newcount" + re.escape(B) + r"pthree\w+.*?\n\}\n", "", t, flags=re.S)
    t = re.sub(re.escape(B) + r"AtBeginDocument\{%\n(?:  .*\n)+?\}\n", "", t)
    t = re.sub(re.escape(B) + r"patchcmd\{.*?\n", "", t, flags=re.S)
    for gone in (B + "usepackage{etoolbox}\n", B + "usepackage{caption}\n",
                 B + "makeatletter\n", B + "makeatother\n"):
        t = t.replace(gone, "")
    t = re.sub(re.escape(B) + r"captionsetup\{[^}]*\}[^\n]*\n", "", t)
    t = re.sub(re.escape(B) + r"setlength\{" + re.escape(B) + r"abovecaptionskip\}[^\n]*\n", "", t)
    print("  reverted the preamble attempts (caption package, hooks, patchcmd, instrumentation)")

    # insert the space after each table's tabular, but only when a caption is what follows it
    lines = t.split("\n")
    out = []
    n = 0
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip() in (B + "end{tabular}}", B + "end{tabular}"):
            nxt = next((l.strip() for l in lines[i + 1:] if l.strip()), "")
            if nxt.startswith(B + "caption"):
                out.append(SPACE.rstrip())
                n += 1
    if n != 5:
        raise SystemExit(f"  ERROR: {n} tabulars followed by a caption, expected 5")

    print(f"  added a 6 pt \\vspace above each of the {n} table captions")
    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text("\n".join(out), encoding="utf-8", newline="")

    check = SUPP.read_text(encoding="utf-8")
    assert check.count(SPACE) == 5, check.count(SPACE)
    for bad in (B + "usepackage{caption}", B + "abovecaptionskip", B + "patchcmd", B + "pthreecapcount",
                B + "@makecaption", B + "AtBeginDocument"):
        assert bad not in check, f"{bad} should have been reverted"
    print("  written and verified: 5 spacers, preamble clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
