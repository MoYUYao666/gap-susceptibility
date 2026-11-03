# -*- coding: utf-8 -*-
r"""Final two fixes: drop an unsupported venue note in Paper A's bibliography, and make P3's label check tree-wide.

1. `yi2025decipher`'s bib note asserted an "(ICML 2026 version)" and a different title. The arXiv record 2510.03268
   (queried 2026-10-17) carries exactly the title/author list already in the entry and says nothing about ICML, so the
   note is unsupported and is removed.

2. P3's source audit warns about four labels "unreferenced in the 10-page text". Two of them
   (`cor:retrieval-specialization`, `thm:repr`) are referenced in `sections/appendix.tex`, which the 10-page build
   deliberately excludes, so the warning is an artefact of the closure. The other two are referenced nowhere in the
   tree and are removed as dead labels. The check becomes tree-wide so the appendix-only references count.

    python tools/_p1193_final_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper合" / "references.bib"
AUDIT = REPO / "paper3" / "paper_ieee" / "audit_check.py"
THEORY = REPO / "paper3" / "paper_ieee" / "sections" / "theory.tex"

NOTE_OLD = r"""  doi       = {10.48550/arXiv.2510.03268},
  note      = {The Convergent Representation of Contrastive Vision-Language Models: Geometry, Modality Gap and Shared Space Alignment (ICML 2026 version)},
"""
NOTE_NEW = r"""  doi       = {10.48550/arXiv.2510.03268},
"""

AUDIT_OLD = r"""    refs = set(re.findall(r"\\ref\{([^}]+)\}", tex))
    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    undefined = sorted(refs - labels)
    check("all \\ref targets defined", not undefined, ", ".join(undefined) or "1:1")
    unused = sorted(labels - refs)
    if unused:
        warn("unreferenced labels in the 10-page text", ", ".join(unused))
"""

AUDIT_NEW = r"""    refs = set(re.findall(r"\\ref\{([^}]+)\}", tex))
    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    undefined = sorted(refs - labels)
    check("all \\ref targets defined", not undefined, ", ".join(undefined) or "1:1")
    # The 10-page closure deliberately excludes the appendix, which is the only place some labels are referenced, so
    # judge "unreferenced" over the whole source tree rather than over the 10-page closure alone.
    tree_refs = set(refs)
    for pattern in ("*.tex", "sections/*.tex", "sections_full/*.tex", "supplementary/*.tex"):
        for p in ROOT.glob(pattern):
            tree_refs |= set(re.findall(r"\\ref\{([^}]+)\}", p.read_text(encoding="utf-8", errors="replace")))
    unused = sorted(labels - tree_refs)
    if unused:
        warn("labels referenced nowhere in the source tree", ", ".join(unused))
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    bib = io.open(BIB, encoding="utf-8").read()
    n1 = bib.count(NOTE_OLD)
    print(f"  bib note: occurrences {n1}")
    if n1 != 1:
        print("  !! abort")
        return 1

    aud = io.open(AUDIT, encoding="utf-8").read()
    n2 = aud.count(AUDIT_OLD)
    print(f"  audit check block: occurrences {n2}")
    if n2 != 1:
        print("  !! abort (audit block not found)")
        return 1
    if "ROOT = Path" not in aud:
        print("  !! audit script has no ROOT constant")
        return 1

    th = io.open(THEORY, encoding="utf-8").read()
    dead = []
    for lab in ("cor:phase-transition", "def:gap-susceptibility"):
        pat = "\\label{%s}" % lab
        if pat in th:
            dead.append(lab)
    print(f"  dead labels to drop: {dead}")

    if not a.apply:
        print("  (dry run)")
        return 0

    bib = bib.replace(NOTE_OLD, NOTE_NEW, 1)
    io.open(BIB, "w", encoding="utf-8", newline="").write(bib)
    print("  references.bib: unsupported note removed")

    aud = aud.replace(AUDIT_OLD, AUDIT_NEW, 1)
    io.open(AUDIT, "w", encoding="utf-8", newline="").write(aud)
    print("  audit_check.py: tree-wide label check")

    for lab in dead:
        th = th.replace("\\label{%s}\n" % lab, "").replace("\\label{%s}" % lab, "")
    io.open(THEORY, "w", encoding="utf-8", newline="").write(th)
    print(f"  sections/theory.tex: dropped {len(dead)} dead labels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
