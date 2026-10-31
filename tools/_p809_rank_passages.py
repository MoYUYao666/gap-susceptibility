# -*- coding: utf-8 -*-
r"""Show the exact Paper A passages that the rank rerun contradicts, with surrounding context.

The rerun shows the change in centroid gap decreasing with rank (monotonically false) while retrieval
is nearly flat. Before editing, this prints each affected sentence verbatim so the replacement can be
worded against the real text.

    python tools/_p809_rank_passages.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"


def main() -> int:
    keys = ["monotonic", "low-rank", "low rank", "rank over the low end", "configured rank",
            "ranks 4, 8 and 16", "32 and 64", "improves monotonically", "rank effect",
            "Effective Rank Saturation", "rank sweep"]
    for f in sorted((PA / "sections").glob("*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        seen = set()
        for key in keys:
            for m in re.finditer(re.escape(key), t, re.I):
                ln = t[:m.start()].count("\n") + 1
                if ln in seen:
                    continue
                seen.add(ln)
                # widen to the enclosing sentence
                a = max(t.rfind(". ", 0, m.start()), t.rfind("\n", 0, m.start()))
                b = t.find(". ", m.start())
                seg = " ".join(t[max(0, a + 1):(b + 1) if b > 0 else m.start() + 300].split())
                print(f"  [{f.name}:{ln}]  key={key!r}")
                print(f"     {seg[:400]}")
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
