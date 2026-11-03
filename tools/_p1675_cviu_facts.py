"""Extract the facts the CVIU package needs from the reframed tree and the recent decision records.

Read-only. Prints:
  * abstract word count of `paper合/reframed/main.tex` (CVIU requires <= 250 words)
  * the highlight bullets already in the tree with their character counts (guide: 3-5, <= 85 chars)
  * the page-budget / reframing numbers quoted by the lead (main text 48 -> 39 pp, 83 pp total)
  * the desk-rejection and transfer-offer facts (for the cover letter)

Usage: python tools/_p1675_cviu_facts.py
"""

from __future__ import annotations

import io
import re
import sys


def read(rel):
    return io.open(rel, encoding="utf-8").read()


def abstract_words(tex):
    i = tex.find("\\begin{abstract}")
    j = tex.find("\\end{abstract}")
    body = tex[i + len("\\begin{abstract}"):j]
    # unwrap simple one-arg macros, then drop remaining backslashes/braces/math dollars
    body = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", body)
    body = re.sub(r"\\[a-zA-Z]+", " ", body)
    body = body.replace("$", " ").replace("{", " ").replace("}", " ")
    toks = [t for t in re.split(r"\s+", body) if re.search(r"[A-Za-z0-9]", t)]
    return len(toks), re.sub(r"\s+", " ", body).strip()


def main() -> int:
    tex = read("paper合/reframed/main.tex")
    n, body = abstract_words(tex)
    print("=== reframed abstract ===")
    print("words:", n, "| CVIU limit 250 ->", "OK" if n <= 250 else "OVER")
    print(body[:1200])
    print()

    print("=== existing highlight bullets (paper合/highlights_nc.txt) ===")
    for line in read("paper合/highlights_nc.txt").splitlines():
        s = line.strip()
        if not s or s.lower() == "highlights":
            continue
        text = s.lstrip("-* ").strip()
        print("  %3d chars  %s" % (len(text), text))
    print()

    for rel, label in (("paper合/reframed/PAGE_BUDGET.md", "PAGE_BUDGET"),
                       ("paper合/reframed/REFRAME_MAP.md", "REFRAME_MAP"),
                       ("docs/paperA_desk_reject_and_transfer_2026-10-26.md", "DESK_REJECT")):
        print("=" * 20, label, "(" + rel + ")", "=" * 20)
        try:
            t = read(rel)
        except OSError as exc:
            print("  missing:", exc)
            continue
        for line in t.splitlines():
            if re.search(r"\b(39|48|83|NEUCOM|transfer|desk|reject|page)\b", line, re.I):
                print("  ", line.strip()[:220])
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
