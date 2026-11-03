# -*- coding: utf-8 -*-
r"""Fix the internal-document citations, covering both the plain and backticked forms.

The per-reviewer _plain.txt files write bare paths; the Markdown twins and the combined letter
wrap them in backticks. Matching both forms is what the earlier two attempts missed.

    python tools/_p660_fix_citations_both.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
DOCS = REPO / "docs" / "P3_RESPONSE_LETTER.md"

BACKTICK = "`"
SUPP = "the downstream tables are in the supplementary material."
PROTO = ("The per-run records carry their own protocol blocks, so the arm, seed and learning "
         "rate of each value can be read off directly.")
PROTO_MD = ("The per-run records carry their own protocol blocks, so the arm, seed and "
            "learning rate of each value can be read off directly.")

FIXES = [
    # Reviewer 1 / combined letter: downstream analysis document
    (re.compile(r"analysis in " + BACKTICK + r"?docs/P3_DOWNSTREAM\.md" + BACKTICK + r"?\."),
     lambda m: "analysis in " + SUPP if BACKTICK in m.group(0) else "analysis in " + SUPP),
    (re.compile(r"Analysis in " + BACKTICK + r"?docs/P3_EXPERIMENTS\.md" + BACKTICK + r"?\."),
     lambda m: "Analysis in " + PROTO_MD),
    # Reviewer 3: statistics document
    (re.compile(r";\s*" + BACKTICK + r"?docs/P3_STATS\.md" + BACKTICK + r"?\."),
     lambda m: "."),
    # Reviewer 3: the assertion location
    (re.compile(r"per-run " + BACKTICK + r"?protocol" + BACKTICK +
                r"? blocks;\s*assertion in " + BACKTICK + r"?tools/_p434_alloc_train\.py" +
                BACKTICK + r"?\."),
     lambda m: "per-run " + BACKTICK + "protocol" + BACKTICK + " blocks; the assertion is "
               "recorded in each per-run block under " + BACKTICK +
               "outputs/analysis/p3_alloc_runs/" + BACKTICK + "."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    targets = sorted({p for p in list(RESP.glob("*")) + [DOCS]
                      if p.is_file() and p.suffix.lower() in (".txt", ".md")})
    total = 0
    for p in targets:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        t2, n = t, 0
        for rx, rep in FIXES:
            t2, k = rx.subn(rep, t2)
            n += k
        if n:
            total += n
            print(f"  {p.name:<46} {n} replacement(s)")
            if a.apply:
                bak = p.with_suffix(p.suffix + ".bak_p660")
                if not bak.exists():
                    shutil.copy2(p, bak)
                io.open(p, "w", encoding="utf-8", newline="").write(t2)
    print(f"  total {total}")
    print()
    print("  Re-check:")
    bad = 0
    for p in targets:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        hits = [k for k in ("docs/P3_DOWNSTREAM", "docs/P3_STATS", "docs/P3_EXPERIMENTS",
                            "tools/_p434") if k in t]
        if hits:
            print(f"    BAD {p.name:<44} {hits}")
            bad += 1
    if bad == 0:
        print("    OK  no response file cites an internal path any more")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
