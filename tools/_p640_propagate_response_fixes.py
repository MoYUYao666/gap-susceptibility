# -*- coding: utf-8 -*-
r"""Propagate the two corrections into every copy of the response material.

Two values changed upstream and must match everywhere the reviewer can see them:

  p = 0.2057  ->  p = 0.21    (the manuscript states 0.21; the archive holds 0.2057)
  corner +3607 +- 514 -> +2344 +- 2426   (the 6-seed values; the manuscript now carries them)
  interior +2241 +- 1291 -> +1477 +- 1563

Files: the three per-reviewer boxes, their Markdown twins, and the combined letter.

    python tools/_p640_propagate_response_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
DOCS = REPO / "docs"

PAIRS = [
    ("p = 0.2057", "p = 0.21"),
    ("0.2057", "0.21"),
    ("+3607 \\pm 514", "+2344 \\pm 2426"),
    ("$+3607 \\pm 514$", "$+2344 \\pm 2426$"),
    ("+3607 ± 514", "+2344 ± 2426"),
    ("+3607", "+2344"),
    ("+2241 \\pm 1291", "+1477 \\pm 1563"),
    ("+2241 ± 1291", "+1477 ± 1563"),
    ("+2241", "+1477"),
]

TARGETS = sorted(list(RESP.glob("*")) + [DOCS / "P3_RESPONSE_LETTER.md"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    plan = []
    for p in TARGETS:
        if not p.is_file() or p.suffix.lower() not in (".txt", ".md"):
            continue
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        t2 = t
        n = 0
        for old, new in PAIRS:
            c = t2.count(old)
            if c:
                t2 = t2.replace(old, new)
                n += c
        if n:
            total += n
            print(f"  {p.relative_to(REPO)!s:<62} {n} replacement(s)")
            plan.append((p, t2))
    print()
    print(f"  total: {total} replacement(s) in {len(plan)} file(s)")
    if not total:
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0
    for p, t2 in plan:
        bak = p.with_suffix(p.suffix + ".bak_p640")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
    print()
    print("  Re-check (stale values remaining):")
    for p, _ in plan:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"    {p.name:<44} 0.2057={t.count('0.2057')} 3607={t.count('3607')} "
              f"2241={t.count('2241')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
