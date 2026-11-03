# -*- coding: utf-8 -*-
"""Make the two Paper A cover letters self-contained and line-break clean.

The cover letters cite three works but carry no bibliography, so they printed "[?, ?, ?]" in
the PDF (a visible defect in the submission materials). The citation is replaced with the
method names, which need no bibliography. The letters also add \\sloppy to remove the 66pt
overfull line caused by the long quoted review title.

    python tools/_p1177_fix_coverletter_cites_layout.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OLD_CITE = "\\cite{zhang2023adalora,wang2024loraga,zanella2024cliplora}"
NEW_TEXT = "(AdaLoRA, LoRA-GA and CLIP-LoRA)"

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()
fails = []
for name in ("cover_letter_nc.tex", "cover_letter.tex"):
    path = PA / name
    text = io.open(path, encoding="utf-8").read()
    changed = []
    if OLD_CITE in text:
        text = text.replace(OLD_CITE, NEW_TEXT)
        changed.append("citation -> method names")
    if "\\sloppy" not in text:
        text = text.replace("\\begin{document}", "\\begin{document}\n\\sloppy", 1)
        changed.append("added \\sloppy")
    if "\\cite" in text:
        fails.append(name + ": a citation command remains")
    if "\\sloppy" not in text:
        fails.append(name + ": \\sloppy missing")
    print("  %s: %s" % (name, ", ".join(changed) if changed else "already current"))
    if changed and a.apply:
        io.open(path, "w", encoding="utf-8", newline="").write(text)
print("RESULT: %d failure(s)" % len(fails))
raise SystemExit(1 if fails else 0)
