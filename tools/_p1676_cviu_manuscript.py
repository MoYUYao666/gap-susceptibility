"""Prepare and build the CVIU manuscript from the reframed tree (idempotent).

Applies the two manuscript-side changes the CVIU submission needs, then rebuilds and verifies:

  1. `\\journal{Computer Vision and Image Understanding}` (the reframed tree ships an empty \\journal).
  2. one wording consistency fix: the abstract still said the Distribution Gap "predicts retrieval
     degradation" while the same abstract later says "we report an association, not a predictor" and the
     body sections were already reworded on 2026-10-25 -> "is associated with retrieval degradation".
     No number changes (abstract 244 -> 247 words, still under the CVIU limit of 250).

The reframed tree is editable; `main_nc.tex` / `main_springer.tex` are NOT touched.

Usage:  python tools/_p1676_cviu_manuscript.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TREE = REPO / "paper合" / "reframed"
MAIN = TREE / "main.tex"

JOURNAL_OLD = "\\journal{}"
JOURNAL_NEW = "\\journal{Computer Vision and Image Understanding}"

WORD_OLD = "the Distribution Gap predicts retrieval degradation"
WORD_NEW = "the Distribution Gap is associated with retrieval degradation"


def abstract_words(tex: str) -> int:
    i = tex.find("\\begin{abstract}")
    j = tex.find("\\end{abstract}")
    body = tex[i + len("\\begin{abstract}"):j]
    body = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", body)
    body = re.sub(r"\\[a-zA-Z]+", " ", body)
    body = body.replace("$", " ").replace("{", " ").replace("}", " ")
    return len([t for t in re.split(r"\s+", body) if re.search(r"[A-Za-z0-9]", t)])


def log_stats(log: Path) -> dict:
    t = io.open(log, encoding="utf-8", errors="replace").read()
    m = re.search(r"Output written on (\S+) \((\d+) pages, (\d+) bytes\)", t)
    return {
        "pages": int(m.group(2)) if m else None,
        "bytes": int(m.group(3)) if m else None,
        "errors": len(re.findall(r"^! ", t, re.M)),
        "undef_ref": len(re.findall(r"LaTeX Warning: Reference[^\n]*undefined", t)),
        "undef_cite": len(re.findall(r"(?:LaTeX|Package natbib) Warning: Citation[^\n]*undefined", t)),
        "overfull_h": len(re.findall(r"^Overfull \\hbox", t, re.M)),
        "overfull_v": len(re.findall(r"^Overfull \\vbox", t, re.M)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rc = 0

    tex = io.open(MAIN, encoding="utf-8").read()
    changed = False
    for old, new, label in ((JOURNAL_OLD, JOURNAL_NEW, "journal name"),
                            (WORD_OLD, WORD_NEW, "abstract wording")):
        if new in tex:
            print("  [skip] %-18s already applied" % label)
            continue
        if tex.count(old) != 1:
            print("  [FAIL] %-18s expected 1 occurrence, found %d" % (label, tex.count(old)))
            rc = 2
            continue
        tex = tex.replace(old, new, 1)
        changed = True
        print("  [edit] %-18s %s" % (label, new[:80]))

    print("  abstract words:", abstract_words(tex), "(CVIU limit 250)")
    if abstract_words(tex) > 250:
        rc = 2

    if not args.apply:
        print("\n(preview; pass --apply to write and build)")
        return rc
    if changed:
        io.open(MAIN, "w", encoding="utf-8", newline="\n").write(tex)
        print("  wrote", MAIN.relative_to(REPO))

    # rebuild: two passes (citations already resolved in main.bbl; bibliography is external)
    for i in (1, 2):
        p = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                           cwd=str(TREE), capture_output=True, text=True)
        print("  pdflatex pass %d: exit %d" % (i, p.returncode))
        if p.returncode != 0:
            rc = 2
    st = log_stats(TREE / "main.log")
    print("  build:", st)
    if st["pages"] != 83:
        print("  WARNING: expected 83 pages (reframed build of 2026-10-26), got", st["pages"])
        rc = 2
    if st["errors"] or st["undef_ref"] or st["undef_cite"] or st["overfull_h"] or st["overfull_v"]:
        print("  WARNING: build not clean")
        rc = 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
