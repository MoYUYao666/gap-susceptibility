# -*- coding: utf-8 -*-
r"""Fix the internal-document citations with whitespace-tolerant matching.

The previous attempt matched the sentences literally, which failed because the combined
letter holds each response on one long line while the per-reviewer files wrap at about 95
columns. Matching on a whitespace-normalised copy handles both.

    python tools/_p659_fix_citations_regex.py [--apply]
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

# patterns written with \s+ wherever the source may wrap
FIXES = [
    (r"analysis in docs/P3_DOWNSTREAM\.md\.",
     "the downstream tables are in the supplementary material."),
    (r"Analysis in docs/P3_EXPERIMENTS\.md\.",
     "The per-run records carry their own protocol blocks, so the arm, seed and learning "
     "rate of each value can be read off directly."),
    (r";\s*docs/P3_STATS\.md\.",
     "."),
    (r"measured_n_trainable_params\s+and\s+the\s+per-run protocol blocks;\s*"
     r"assertion in tools/_p434_alloc_train\.py\.",
     "measured_n_trainable_params, and the assertion recorded in each per-run protocol "
     "block under outputs/analysis/p3_alloc_runs/."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    targets = [p for p in sorted(list(RESP.glob("*")) + [DOCS])
               if p.is_file() and p.suffix.lower() in (".txt", ".md")]
    total = 0
    for p in targets:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        t2, n = t, 0
        for pat, new in FIXES:
            t2, k = re.subn(pat, lambda _m, s=new: s, t2)
            n += k
        if n:
            total += n
            print(f"  {p.name:<46} {n} replacement(s)")
            if a.apply:
                bak = p.with_suffix(p.suffix + ".bak_p659")
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
