# -*- coding: utf-8 -*-
r"""Strict provenance matching: find archives that contain every reported number of a table/figure caption.

For each float, extract caption numbers (length >= 2) and require a candidate archive to contain all of them; candidates
are ranked by file size (smaller = more specific). This gives high-precision mappings that can be stated in a provenance
appendix without manual guessing.

Output: outputs/analysis/provenance_strict.json

    python tools/_p1423_provenance_strict.py --apply
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
OUT = os.path.join(REPO, "outputs", "analysis", "provenance_strict.json")
NUM_RE = re.compile(r"(?<![\w.])(\d{2,}(?:\.\d+)?)(?![\w.])")
YEAR_RE = re.compile(r"^(19|20)\d{2}$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    draft = json.load(io.open(DRAFT, encoding="utf-8"))
    arches = {}
    for pat in ("outputs/*.json", "outputs/analysis/*.json", "outputs/*/*.json"):
        for f in glob.glob(os.path.join(REPO, pat)):
            try:
                arches[f] = io.open(f, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
    out = {}
    for name, items in draft.items():
        rows = []
        for it in items:
            cap = it.get("caption", "")
            toks = [t for t in NUM_RE.findall(cap) if not YEAR_RE.match(t)]
            toks = sorted(set(toks), key=lambda x: -len(x))[:8]
            cands = []
            if len(toks) >= 2:
                for f, txt in arches.items():
                    if all(re.search(r"(?<![\d.])" + re.escape(t) + r"(?![\d.])", txt) for t in toks):
                        cands.append((os.path.getsize(f), os.path.relpath(f, REPO)))
                cands.sort()
            row = {"kind": it["kind"], "label": it["label"], "caption": cap[:160],
                   "tokens": toks, "archives": [c[1] for c in cands[:3]],
                   "figure_scripts": it.get("scripts", []),
                   "figure_archive": it.get("archive")}
            rows.append(row)
        out[name] = rows
        solved = sum(1 for r in rows if r["archives"] or r["figure_archive"])
        print(f"  {name}: {len(rows)} floats; strictly matched: {solved}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
