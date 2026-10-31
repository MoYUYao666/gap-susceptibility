# -*- coding: utf-8 -*-
r"""Provenance from labels: for every float, find the tools script that mentions its label and the JSON archive it cites.

Most floats were inserted by scripts that embed the caption and the archive path, so searching the label across tools/ and
docs/ recovers the mapping. This script reports, for every float, the candidate scripts and the archives cited near the label.

Output: outputs/analysis/provenance_from_labels.json

    python tools/_p1422_provenance_from_labels.py --apply
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
OUT = os.path.join(REPO, "outputs", "analysis", "provenance_from_labels.json")
JSON_RE = re.compile(r"outputs/[\w./-]+\.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    draft = json.load(io.open(DRAFT, encoding="utf-8"))
    files = [f for f in glob.glob(os.path.join(REPO, "tools", "*.py"))]
    texts = {f: io.open(f, encoding="utf-8", errors="ignore").read() for f in files}
    result = {}
    for name, items in draft.items():
        rows = []
        for it in items:
            lab = it.get("label")
            row = {"kind": it["kind"], "label": lab, "caption": it["caption"][:160],
                   "scripts": [], "archives": [], "figure_scripts": it.get("scripts", []),
                   "figure_archive": it.get("archive")}
            if lab:
                for f, t in texts.items():
                    if lab in t:
                        i = t.find(lab)
                        near = t[max(0, i - 4000): i + 4000]
                        arcs = sorted(set(JSON_RE.findall(near)))[:6]
                        row["scripts"].append(os.path.relpath(f, REPO))
                        for arc in arcs:
                            if arc not in row["archives"]:
                                row["archives"].append(arc)
            rows.append(row)
        result[name] = rows
        solved = sum(1 for r in rows if r["archives"] or r["figure_archive"])
        print(f"  {name}: {len(rows)} floats; with archive candidate: {solved}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(result, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
