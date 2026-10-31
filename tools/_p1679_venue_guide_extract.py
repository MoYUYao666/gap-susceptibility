"""Extract the decision facts for the four Paper A second-round candidates (read-only).

Inputs (captured 2026-10-26 through the visible-Edge CDP route; headless is blocked):
  %TEMP%/mjl_{is,ijcv,ai2,cc}.txt          Master Journal List result pages
  %TEMP%/guide_{is,ijcv,ai,cc}.txt         submission guidelines

Prints, per journal, the MJL verdict lines and the guide passages that decide feasibility
(page/word limit, abstract, keywords, highlights, vitae/photo, anonymisation, LaTeX, references,
data statement, artwork, spacing/line numbers, aims/scope).

Usage: python tools/_p1679_venue_guide_extract.py [--journal is|ijcv|ai|cc]
"""

from __future__ import annotations

import io
import os
import re
import sys

T = os.environ.get("TEMP", "/tmp")

JOURNALS = {
    "is": ("Information Sciences", "mjl_is.txt", "guide_is.txt"),
    "ijcv": ("International Journal of Computer Vision", "mjl_ijcv.txt", "guide_ijcv.txt"),
    "ai": ("Applied Intelligence", "mjl_ai2.txt", "guide_ai.txt"),
    "cc": ("Cognitive Computation", "mjl_cc.txt", "guide_cc.txt"),
}

PATTERNS = [
    ("LENGTH", r"\bpages?\b|page limit|no less than|no more than|word limit|words?\b"),
    ("ABSTRACT", r"abstract"),
    ("KEYWORDS", r"keyword"),
    ("HIGHLIGHTS", r"highlight"),
    ("VITAE/PHOTO", r"vitae|biograph|bio-sketch|biosketch|photograph|passport"),
    ("ANONYM", r"anonym|double-blind|blind review|single-blind"),
    ("LATEX/FORMAT", r"latex|tex\b|double-spac|single column|single-column|line number|font"),
    ("REFERENCES", r"reference style|citation style|reference list|crossref|doi"),
    ("DATA", r"data statement|data availability|option [abcd]\b|research data"),
    ("ARTWORK", r"artwork|separate file|figure|illustration"),
    ("SCOPE", r"aims and scope|aims & scope|scope of the journal|publishes"),
]


def lines(path):
    p = os.path.join(T, path)
    if not os.path.exists(p):
        return []
    return [l.strip() for l in io.open(p, encoding="utf-8", errors="replace").read().splitlines()]


def show(name, key):
    title, mjl, guide = JOURNALS[key]
    print("#" * 78)
    print("##", name)
    print("#" * 78)

    ml = lines(mjl)
    print("\n--- MJL ---")
    if not ml:
        print("  (capture missing)")
    else:
        for l in ml:
            if re.search(r"Web of Science Core Collection|Citation Index|Additional Web of Science|"
                         r"ISSN|Journals Relevant|Relevant To|TITLE:|MARKER:", l, re.I) and len(l) < 260:
                print("  ", l)
    gl = lines(guide)
    print("\n--- GUIDE (%d lines) ---" % len(gl))
    if not gl:
        print("  (capture missing)")
        return
    for label, pat in PATTERNS:
        rx = re.compile(pat, re.I)
        hits = [(i, l) for i, l in enumerate(gl) if rx.search(l) and len(l) > 25]
        if not hits:
            print("\n  [%s] -- no matching line" % label)
            continue
        print("\n  [%s] %d hit(s)" % (label, len(hits)))
        for i, l in hits[:12]:
            print("   %4d %s" % (i, l[:330]))


def main() -> int:
    which = sys.argv[2] if len(sys.argv) == 3 and sys.argv[1] == "--journal" else None
    for key, (name, _, _) in JOURNALS.items():
        if which and key != which:
            continue
        show(name, key)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
