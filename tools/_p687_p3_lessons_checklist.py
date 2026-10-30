# -*- coding: utf-8 -*-
r"""Derive the check list from the P3 reviewer responses, and read Paper A's stale statements.

The P3 revision produced a set of claims the reviewers forced us to withdraw or downgrade. If
any of those claims survives in Paper A, the same objection applies there - and Paper A is
about to be submitted, so this is the moment to find them.

This extracts the withdrawal/downgrade statements from the P3 response boxes and prints them as
a check list, then shows the exact text of Paper A's two data availability statements.

    python tools/_p687_p3_lessons_checklist.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "p3_lessons_checklist.json"

# sentences in the P3 responses that state a withdrawal or downgrade
KEYS = [r"we (?:have )?withdraw", r"withdrawn", r"downgrad", r"no longer claim",
        r"does not survive", r"we report that rather than hide", r"belongs to the protocol",
        r"not a proxy", r"we do not claim"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 104)
    print("A. what the P3 reviewers forced us to withdraw or downgrade")
    print("=" * 104)
    items = []
    for p in sorted(P3RESP.glob("*_plain.txt")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        t = re.sub(r"\s+", " ", t)
        for m in re.finditer("|".join(KEYS), t, re.I):
            s = t.rfind(". ", 0, m.start())
            e = t.find(". ", m.start())
            sent = t[s + 1:e + 1].strip()
            if 40 < len(sent) < 420 and sent not in items:
                items.append(sent)
    for i, s in enumerate(items, 1):
        print(f"  {i:>2}. {s[:300]}")

    print()
    print("=" * 104)
    print("B. Paper A: the two data availability statements, verbatim from the source")
    print("=" * 104)
    main = PA / "main_nc.tex"
    t = io.open(main, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"data availability", t, re.I):
        ln = t[:m.start()].count("\n") + 1
        s = t.rfind("\n", 0, max(0, m.start() - 400))
        seg = t[max(0, m.start() - 200):m.start() + 900]
        print(f"  --- main_nc.tex line {ln} ---")
        print(seg)
        print()

    print("=" * 104)
    print("C. sections/conclusion.tex statement")
    print("=" * 104)
    c = io.open(PA / "sections" / "conclusion.tex", encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"data availability", c, re.I):
        ln = c[:m.start()].count("\n") + 1
        print(f"  line {ln}: {c[max(0, m.start() - 120):m.start() + 240]!r}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"p3_withdrawals": items}, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
        print(f"  ({len(items)} withdrawal/downgrade statements extracted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
