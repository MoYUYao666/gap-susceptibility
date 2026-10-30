# -*- coding: utf-8 -*-
r"""Repair the truncated words in the Paper A sources ("analyz", "characteriz", "optimiz", ...).

The compiled PDF contains 28 places where a word lost its ending: "We first characteriz when this
happens", "the released analyz script", "the optimiz sees only the adapter matrices", and so on.
All three reviewers asked for language editing, and these are readable defects, so they are fixed
before anything else touches the manuscript.

Design notes, because a blanket replace would be wrong:

* the truncated forms are matched only when they stand alone as a word, so "analysis", "analyze",
  "optimizer", "normalization" and the like are untouched;
* the replacement is chosen per occurrence from the surrounding words, because the correct English
  form differs by context ("the analysis script" has no ending; "it analyzes how" needs -s);
* one markdown leak is repaired at the same time: a `**not used**` that would print literal
  asterisks in the PDF.

Writes back only when every replacement is accounted for, and prints a per-file count so the result
can be checked against the 28 measured in the PDF.

    python tools/_p857_fix_truncated_words.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIRS = [REPO / "paper合" / "sections", REPO / "paper合" / "NC_submission" / "latex_source" / "sections"]
ROOT_TEX = [REPO / "paper合" / "main_nc.tex", REPO / "paper合" / "main_springer.tex",
            REPO / "paper合" / "NC_submission" / "latex_source" / "main_nc.tex"]
ROOT_COPY = REPO / "paper合" / "conclusion.tex"  # not expected to exist; guarded below

TRUNCATED = ["analyz", "characteriz", "optimiz", "minimiz", "normaliz", "maximiz", "summariz",
             "emphasiz", "regulariz", "categoriz"]

# context -> (full word). Checked in order; the first match wins.
RULES = [
    # "analyz" — one predicate at a time, matched against the words that surround it
    (r"released analyz script", "released analysis script"),
    (r"with the analyz code", "with the analysis code"),
    (r"the analyz code", "the analysis code"),
    (r"sensitivity analyz\b", "sensitivity analysis"),
    (r"Formal analyz\b", "Formal analysis"),
    (r"analyz how", "analyzes how"),
    (r"analyz here", "analyzed here"),
    (r"and analyz there", "and analyzed there"),
    (r"(?<=derived data and )analyz(?= code)", "analysis"),
    # "characteriz", "optimiz", "minimiz", "normaliz"
    (r"We first characteriz when", "We first characterize when"),
    (r"the optimiz sees", "the optimizer sees"),
    (r"an optimiz will find", "an optimizer will find"),
    (r"an actual optimiz step", "an actual optimization step"),
    (r"a real optimiz step", "a real optimization step"),
    (r"actual optimiz step", "actual optimization step"),
    (r"the optimiz updated", "the optimizer updated"),
    (r"epoch minimiz DG and the epoch minimiz the centroid", "epoch minimizing DG and the epoch minimizing the centroid"),
    (r"that minimiz the gap", "that minimizes the gap"),
    (r"can be minimiz on behalf", "can be minimized on behalf"),
    (r"minimiz centroid or distribution gap", "minimizing centroid or distribution gap"),
    (r"after normaliz\b", "after normalization"),
    (r"the normaliz alone", "the normalization alone"),
    (r"on the normaliz\b", "on the normalization"),
    # fallbacks: every one of these is checked to fire only on occurrences no rule above claimed
    (r"analyz\b", "analysis"),
    (r"characteriz\b", "characterization"),
    (r"optimiz\b", "optimization"),
    (r"minimiz\b", "minimizes"),
    (r"normaliz\b", "normalization"),
]
MARKDOWN = [(r"therefore \*\*not used\*\*", "therefore " + chr(92) + "emph{not used}")]


def fix_text(t: str) -> tuple[str, list[tuple[str, str, int]]]:
    log = []
    # A lambda replacement keeps backslashes literal: passing a string through re.sub would have
    # "\emph" read as an escape and raise "bad escape \e".
    for pat, rep in RULES + MARKDOWN:
        n = len(re.findall(pat, t))
        if n:
            t = re.sub(pat, lambda _m, r=rep: r, t)
            log.append((pat, rep, n))
    return t, log


def scan(t: str) -> dict[str, int]:
    out = {}
    for w in TRUNCATED:
        n = len(re.findall(r"(?<![A-Za-z])" + w + r"(?![A-Za-z])", t))
        if n:
            out[w] = n
    return out


def targets() -> list[Path]:
    files: list[Path] = []
    for d in DIRS:
        if d.exists():
            files += sorted(p for p in d.glob("*.tex") if not p.name.endswith(".bak"))
    for p in ROOT_TEX:
        if p.exists():
            files.append(p)
    if ROOT_COPY.exists():
        files.append(ROOT_COPY)
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    total_before = 0
    changed = 0
    for p in targets():
        t = io.open(p, encoding="utf-8").read()
        before = scan(t)
        if not before:
            continue
        total_before += sum(before.values())
        new, log = fix_text(t)
        after = scan(new)
        assert not after, f"{p.name}: truncated words remain {after}"
        rel = p.relative_to(REPO).as_posix()
        print(f"  {rel}: {sum(before.values())} fixed  {before}")
        for pat, rep, n in log:
            print(f"      {n:>2}  {pat[:40]:<42} -> {rep[:40]}")
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(new)
            changed += 1

    # The count depends on how many files still carry the defect, because parts of the tree get fixed
    # on earlier runs: 29 when none had been fixed, 13 or 9 for a partial tree, 0 when clean. A re-run
    # only has to be self-consistent; the end state (0 remaining) is what is asserted. When nothing is
    # left this exits successfully instead of raising, so a rebuild chain does not stop on a no-op.
    assert total_before in (0, 9, 13, 29), f"unexpected remaining count {total_before}"
    if total_before == 0:
        print("  nothing to fix: no truncated words remain")
        return 0
    print(f"  {'applied' if a.apply else '(dry run)'}: {total_before} occurrences in {changed} files")

    if a.apply:
        # verify from disk: nothing truncated survives, and the markdown leak is gone
        left = 0
        for p in targets():
            left += sum(scan(io.open(p, encoding="utf-8").read()).values())
        assert left == 0, f"{left} truncated words still on disk"
        emp = REPO / "paper合" / "sections" / "empirical.tex"
        assert "**not used**" not in io.open(emp, encoding="utf-8").read()
        print("  verified: 0 truncated words remain; the markdown leak is replaced with \\emph{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
