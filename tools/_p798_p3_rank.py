# -*- coding: utf-8 -*-
r"""Read what P3 claims about rank, to judge what the adapter-scope defect does to it.

P3 reports a critical rank r_c and rank-scaling behaviour. If those came from the defective adapter
path, the rank was not the knob that was varied. This collects the relevant sentences before any
edit is attempted.

    python tools/_p798_p3_rank.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"


def main() -> int:
    keys = ["r_c", "critical rank", "phase transition", "rank scaling", "monotonic",
            "rank $r$", "ranks ", "rank of", "low-rank", "adapter rank", "rank 4", "rank 8",
            "rank 16", "rank 32", "rank 64", "L2 norm", "per-rank"]
    for f in sorted((P3 / "sections").glob("*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        hits = []
        for m in re.finditer(r"[^.\n]{0,170}", t):
            seg = " ".join(m.group(0).split())
            if len(seg) < 60:
                continue
            if any(k in seg for k in keys) and re.search(r"rank", seg, re.I):
                ln = t[:m.start()].count("\n") + 1
                hits.append((ln, seg))
        if hits:
            print("=" * 104)
            print(f"{f.name}   ({len(hits)} fragment(s))")
            print("=" * 104)
            for ln, s in hits[:6]:
                print(f"  L{ln}: {s[:270]}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
