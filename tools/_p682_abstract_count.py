# -*- coding: utf-8 -*-
r"""Count the Paper A abstract exactly, and say how many words have to go.

The package README asserts 246 words; measuring the compiled PDF gives 260-263. The
Neurocomputing guide caps the abstract at 250 words, so the difference decides whether the
package can be submitted as it stands.

This counts in the way a copy-editor would (hyphenated line breaks joined, layout artefacts
dropped) and reports the number of words over the limit.

    python tools/_p682_abstract_count.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
NC = PA / "NC_submission"
OUT = REPO / "outputs" / "analysis" / "paperhe_abstract_count.json"
LIMIT = 250


def pdftotext(p: Path) -> str:
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def clean(s: str) -> str:
    s = s.replace("\u00ad", "")                      # soft hyphens
    s = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", s)     # hyphenated line break -> join
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    man = pdftotext(NC / "Manuscript.pdf")

    # the abstract runs from the word Abstract to the Keywords line
    m = re.search(r"\bAbstract\b(.*?)\bKeywords\b", man, re.S | re.I)
    if not m:
        print("  could not locate the abstract in the PDF")
        return 1
    abs_txt = clean(m.group(1))
    words = abs_txt.split()
    n = len(words)
    print(f"  abstract: {n} words, {len(abs_txt)} characters   (limit {LIMIT})")
    print(f"  {'WITHIN the limit' if n <= LIMIT else f'OVER by {n - LIMIT} words'}")
    print()
    print("  " + abs_txt)
    print()

    if n > LIMIT:
        print("=" * 104)
        print("words that could go, with the sentence each sits in")
        print("=" * 104)
        sents = re.split(r"(?<=[.!?])\s+", abs_txt)
        for s in sents:
            print(f"  [{len(s.split()):>3} words] {s[:150]}")

    print()
    print("=" * 104)
    print("what the source file says")
    print("=" * 104)
    tex = io.open(PA / "main_nc.tex", encoding="utf-8", errors="replace").read()
    am = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if am:
        raw = am.group(1)
        raw = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", lambda mm: mm.group(1), raw)
        raw = re.sub(r"\$[^$]*\$", " MATH ", raw)
        tex_txt = clean(raw)
        print(f"  main_nc.tex abstract: {len(tex_txt.split())} words")
        print(f"  (the PDF count includes the keywords line if the boundary was missed)")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"words": n, "limit": LIMIT, "over_by": max(0, n - LIMIT),
             "text": abs_txt}, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
