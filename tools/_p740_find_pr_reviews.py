# -*- coding: utf-8 -*-
r"""Find the Pattern Recognition rejection letter or its reviewer comments anywhere in the workspace.

The operator asked what remains to be addressed from the PR rejection. The file has not been found
by name, so this searches by content: files that read like a decision letter or referee report
(reviewer numbering, "Comments to the Author", "recommend", "reject", "referee").

    python tools/_p740_find_pr_reviews.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKIP = re.compile(r"\\publish_clean\\|\\\.git\\|\\node_modules\\|\\backups\\|\\_superseded|"
                  r"\\\.worktrees\\|\\tools\\|\\outputs\\|\\paper3\\|\\paper_a1|\\paper_a2|"
                  r"\\备选\\")

# phrases that occur in a decision letter or referee report but not in our own audits
STRONG = [
    r"Comments to the Author",
    r"Reviewer\s*#?\s*\d",
    r"Reviewer'?s? comment",
    r"Recommendation",
    r"we regret to inform",
    r"referee",
    r"Editor'?s? comment",
    r"Decision Letter",
    r"decision on your manuscript",
    r"required reviews completed",
]
WEAK = [r"\breject", r"\breferee", r"reviewer"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = [p for p in REPO.rglob("*") if p.is_file() and p.suffix.lower() in
             (".txt", ".md", ".json", ".eml", ".html", ".rtf")]
    print(f"  scanning {len(files)} text-ish files")
    print()
    results = []
    for p in files:
        rel = str(p)
        if SKIP.search(rel):
            continue
        try:
            if p.stat().st_size > 3_000_000:
                continue
            t = io.open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        strong = [s for s in STRONG if re.search(s, t, re.I)]
        weak = [s for s in WEAK if re.search(s, t, re.I)]
        if strong:
            results.append((p, strong, weak, len(t)))
    print(f"  {len(results)} file(s) contain a strong decision-letter phrase:")
    for p, strong, weak, n in sorted(results, key=lambda r: -len(r[1])):
        print()
        print(f"  {p.relative_to(REPO)}   ({n:,} chars)")
        print(f"     strong: {strong[:6]}")
        print(f"     weak  : {weak}")
        t = io.open(p, encoding="utf-8", errors="ignore").read()
        for s in strong[:2]:
            for m in list(re.finditer(s, t, re.I))[:2]:
                ln = t[:m.start()].count("\n") + 1
                seg = " ".join(t[max(0, m.start() - 100):m.start() + 300].split())
                print(f"     L{ln}: ...{seg[:330]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
