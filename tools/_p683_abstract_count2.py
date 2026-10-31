# -*- coding: utf-8 -*-
r"""Count the Paper A abstract properly, two independent ways, treating maths as whole words.

The previous attempt reported 260 because the PDF layout put the corresponding-author footnote
and a second-column fragment inside the slice, and because "R2 = 0.949" was counted as three
words. The source file gives 246.

Two methods, so the answer does not depend on one parser:
  A. the LaTeX source, with each inline math expression replaced by a single token
  B. the compiled PDF, with the footnote and column-bleed lines removed first

    python tools/_p683_abstract_count2.py [--apply]
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


def count_words(s: str) -> int:
    """A word is a run of non-space characters; maths is pre-tokenised, so this is fine."""
    return len([w for w in s.split() if re.search(r"[A-Za-z0-9]", w)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    result = {}

    print("=" * 104)
    print("A. from the LaTeX source (maths collapsed to one token each)")
    print("=" * 104)
    tex = io.open(PA / "main_nc.tex", encoding="utf-8", errors="replace").read()
    am = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if not am:
        print("  abstract environment not found")
        return 1
    body = am.group(1)
    # inline and display maths -> one token
    body = re.sub(r"\$[^$]*\$", " MATHTOKEN ", body)
    body = re.sub(r"\\\[.*?\\\]", " MATHTOKEN ", body, flags=re.S)
    # wrapper commands keep their argument
    body = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", lambda m: m.group(1), body)
    body = re.sub(r"\\[a-zA-Z]+", " ", body)
    body = body.replace("{", " ").replace("}", " ")
    body = re.sub(r"\s+", " ", body).strip()
    a_words = count_words(body)
    print(f"  words: {a_words}   ({'OK' if a_words <= LIMIT else 'OVER by %d' % (a_words - LIMIT)})")
    result["from_tex"] = a_words
    print()
    print("  " + body[:1200])

    print()
    print("=" * 104)
    print("B. from the compiled PDF (footnote and column bleed removed)")
    print("=" * 104)
    r = subprocess.run(["pdftotext", "-q", "-layout", str(NC / "Manuscript.pdf"), "-"],
                       capture_output=True)
    man = r.stdout.decode("utf-8", errors="replace")
    m = re.search(r"\bAbstract\b(.*?)\bKeywords\b", man, re.S | re.I)
    if not m:
        print("  abstract boundaries not located")
    else:
        seg = m.group(1)
        # drop the footnote and anything that looks like the second column bleeding in
        seg = re.sub(r"∗\s*Corresponding author.*", " ", seg, flags=re.S)
        seg = re.sub(r"Email address:\s*\S+\s*\([^)]*\)", " ", seg)
        seg = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", seg)
        seg = re.sub(r"\s+", " ", seg).strip()
        b_words = count_words(seg)
        print(f"  words: {b_words}   ({'OK' if b_words <= LIMIT else 'OVER by %d' % (b_words - LIMIT)})")
        result["from_pdf"] = b_words
        print()
        print("  " + seg[:1200])

    print()
    print("=" * 104)
    print("verdict")
    print("=" * 104)
    vals = [v for v in (result.get("from_tex"), result.get("from_pdf")) if v]
    if vals:
        print(f"  counts: {vals}")
        print(f"  limit : {LIMIT}")
        worst = max(vals)
        print(f"  {'COMPLIANT' if worst <= LIMIT else 'NEEDS TRIMMING'}: worst count {worst}, "
              f"{'margin %d' % (LIMIT - worst) if worst <= LIMIT else 'over by %d' % (worst - LIMIT)}")
        result["worst"] = worst
        result["compliant"] = worst <= LIMIT

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(result, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
