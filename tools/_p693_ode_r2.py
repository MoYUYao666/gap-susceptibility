# -*- coding: utf-8 -*-
r"""Find out what the manuscript actually claims as its ODE fit quality.

The highlights bullet says "an ODE predicts gap trajectories at median R2 of 0.97" in the txt
files and 0.96 in highlights_nc.pdf, and the manuscript contains both 0.96 (five times) and
0.97 (four times). A bullet that quotes the wrong one is the kind of error a reviewer catches.

This prints every sentence in the manuscript that carries either number, so the bullet can be
written to match what the paper says.

    python tools/_p693_ode_r2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "paperhe_r2.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hits = {}
    files = [PA / "main_nc.tex"] + sorted((PA / "sections").glob("*.tex"))
    for p in files:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"0\.9[4-9]\d?", t):
            ln = t[:m.start()].count("\n") + 1
            # sentence-ish context
            s = max(t.rfind(". ", 0, m.start()), t.rfind("\n", 0, m.start()))
            e = min([x for x in (t.find(". ", m.start()), t.find("\n", m.start()))
                     if x > 0] or [len(t)])
            seg = " ".join(t[max(0, s + 1):e + 1].split())
            hits.setdefault(p.name, []).append((m.group(0), ln, seg[:320]))

    for f, rows in hits.items():
        print("=" * 104)
        print(f)
        print("=" * 104)
        for val, ln, seg in rows:
            print(f"  {val}  (line {ln})")
            print(f"     {seg}")
        print()

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({f: [{"value": v, "line": l, "context": s} for v, l, s in r]
                        for f, r in hits.items()}, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
