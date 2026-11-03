# -*- coding: utf-8 -*-
r"""Provenance v4: recursive archive search with lenient token matching.

Includes nested outputs/**/*.json archives (many results live under outputs/<experiment>/...), and accepts an archive when it
contains all but at most two of the caption numbers (ranked by file size). Larger coverage, still auditable: every hit keeps
the token list that was matched.

Output: outputs/analysis/provenance_v4.json

    python tools/_p1427_provenance_v4.py --apply
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFT = os.path.join(REPO, "outputs", "analysis", "provenance_map_v2.json")
OUT = os.path.join(REPO, "outputs", "analysis", "provenance_v4.json")
NUM_RE = re.compile(r"(?<![\w.])(-?\d+\.\d+|\d{2,})(?![\w.])")
YEAR_RE = re.compile(r"^(19|20)\d{2}$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    draft = json.load(io.open(DRAFT, encoding="utf-8"))
    arches = {}
    for f in glob.glob(os.path.join(REPO, "outputs", "**", "*.json"), recursive=True):
        try:
            if os.path.getsize(f) > 3_000_000:
                continue
            arches[f] = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
    print("  archives loaded:", len(arches))
    out = {}
    for name, items in draft.items():
        rows = []
        for it in items:
            cap = it.get("caption", "")
            toks = sorted(set(t for t in NUM_RE.findall(cap) if not YEAR_RE.match(t)), key=len, reverse=True)[:6]
            cands = []
            if len(toks) >= 2:
                for f, txt in arches.items():
                    hit = sum(1 for t in toks if re.search(r"(?<![\d.])" + re.escape(t) + r"(?![\d.])", txt))
                    if hit >= len(toks) - 2 and hit >= 2:
                        cands.append((os.path.getsize(f), hit, os.path.relpath(f, REPO)))
                cands.sort(key=lambda x: (-x[1], x[0]))
            rows.append({"kind": it["kind"], "label": it["label"], "caption": cap[:150],
                         "tokens": toks, "archives": [c[2] for c in cands[:3]],
                         "hits": [c[1] for c in cands[:3]],
                         "figure_scripts": it.get("scripts", []), "figure_archive": it.get("archive")})
        out[name] = rows
        solved = sum(1 for r in rows if r["archives"] or r["figure_archive"])
        print(f"  {name}: {len(rows)} floats; candidates: {solved}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
