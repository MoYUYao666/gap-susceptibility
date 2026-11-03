# -*- coding: utf-8 -*-
r"""Read the rank-related claims in Paper A, so the wording can be corrected accurately.

The adapter-scope defect means the archived rank ablations varied a knob that controlled 0.13 percent
of the trainable parameters. Before rewording anything, this collects what the paper actually claims
about rank.

    python tools/_p796_rank_claims.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"


def main() -> int:
    keys = ["monotonic", "rank sweep", "rank of", "configured rank", "low-rank", "rank-effect",
            "rank effect", "rank $r$", "ranks 4, 8", "rank 8", "rank 16", "rank 32", "rank 64",
            "rank increases", "rank decreases", "rank interacts"]
    for f in sorted((PA / "sections").glob("*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        hits = []
        for m in re.finditer(r"[^.\n]{0,170}", t):
            seg = m.group(0)
            if any(k in seg for k in keys) and re.search(r"rank", seg, re.I):
                s = " ".join(seg.split())
                if len(s) > 60:
                    ln = t[:m.start()].count("\n") + 1
                    hits.append((ln, s))
        if hits:
            print("=" * 104)
            print(f"{f.name}  ({len(hits)} sentence fragment(s))")
            print("=" * 104)
            for ln, s in hits[:8]:
                print(f"  L{ln}: {s[:260]}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
