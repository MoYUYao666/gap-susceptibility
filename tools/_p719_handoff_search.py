# -*- coding: utf-8 -*-
r"""Search HANDOFF.md for the provenance of Paper A's five unsourced numbers.

The archive search found no supporting field, but the handoff document records what each working
session did. If the numbers were produced by a script, the handoff usually names it.

Values: 117 (mechanism experiments), 95 (strict-freezing controls), 221 (catalogue runs),
383 (validation experiments), 0.29 (CR1 standard error).

    python tools/_p719_handoff_search.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
H = REPO / "HANDOFF.md"

TARGETS = {
    "117": ["mechanism", "机制", "117"],
    "95": ["strict-freezing", "strict freeze", "冻结", "95 "],
    "221": ["catalogue", "catalog", "目录", "221"],
    "383": ["validation", "验证", "383"],
    "0.29": ["standard error", "标准误", "CR1", "0.29"],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(H, encoding="utf-8", errors="replace").read()
    lines = t.splitlines()
    print(f"  HANDOFF.md: {len(lines)} lines, {len(t):,} characters")
    print()

    for val, keys in TARGETS.items():
        print("=" * 112)
        print(f"  {val}   (context keys: {keys[:3]})")
        print("=" * 112)
        hits = []
        for i, l in enumerate(lines, 1):
            if val not in l:
                continue
            # require the line to be about the same subject
            if not any(k.lower() in l.lower() for k in keys[:-1] or keys):
                continue
            hits.append((i, l.strip()))
        if not hits:
            # fall back: any line containing the value, showing the first few
            any_hits = [(i, l.strip()) for i, l in enumerate(lines, 1) if val in l]
            print(f"  no context-qualified hit; {len(any_hits)} line(s) contain the value")
            for i, l in any_hits[:6]:
                print(f"     L{i}: {l[:150]}")
        else:
            print(f"  {len(hits)} context-qualified line(s)")
            for i, l in hits[:10]:
                print(f"     L{i}: {l[:170]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
