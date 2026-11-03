# -*- coding: utf-8 -*-
r"""Locate every place in the two manuscripts that needs the corrected wording.

    python tools/_p795_locate_edits.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "edit_locations.json"

PATTERNS = {
    "COCO near-random / R@1<0.001": r"[^.\n]{0,160}(?:R@1[^.\n]{0,40}(?:<|below)\s*\$?0\.001|"
                                    r"near[- ]random)[^.\n]{0,160}",
    "COCO cross-dataset claim": r"[^.\n]{0,140}COCO[^.\n]{0,160}",
    "rank sweep / rank effect": r"[^.\n]{0,140}(?:rank\s+\$?r|rank\s+\d|rank sweep|"
                                r"monotonic[^.\n]{0,40}rank)[^.\n]{0,160}",
    "LoRA as the method": r"[^.\n]{0,100}LoRA[^.\n]{0,150}",
    "trainable-parameter share": r"[^.\n]{0,120}(?:0\.1\s*\\?%|0\.13\s*\\?%|trainable parameters|"
                                 r"parameter[- ]efficien)[^.\n]{0,150}",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}
    for label, root in (("Paper A", REPO / "paper合"), ("P3", REPO / "paper3" / "paper_ieee")):
        print("=" * 108)
        print(f"{label}")
        print("=" * 108)
        per = {}
        for name, pat in PATTERNS.items():
            rows = []
            for f in sorted(root.rglob("*.tex")):
                t = io.open(f, encoding="utf-8", errors="replace").read()
                for m in re.finditer(pat, t, re.S):
                    seg = " ".join(m.group(0).split())
                    if len(seg) < 30:
                        continue
                    ln = t[:m.start()].count("\n") + 1
                    rows.append({"file": str(f.relative_to(root)), "line": ln,
                                 "text": seg[:260]})
            per[name] = rows
            print()
            print(f"  --- {name}: {len(rows)} hit(s) ---")
            key_files = {}
            for r in rows:
                key_files[r["file"]] = key_files.get(r["file"], 0) + 1
            for f, c in sorted(key_files.items(), key=lambda kv: -kv[1])[:6]:
                print(f"      {f:<38} {c}")
            for r in rows[:2]:
                print(f"      [{r['file']}:{r['line']}] {r['text'][:190]}")
        report[label] = per
    print()
    print("=" * 108)
    print("edit plan")
    print("=" * 108)
    print("  Paper A: COCO retrieval statement, rank-effect wording, method naming, param share")
    print("  P3     : method naming and rank-effect wording (PDF already submitted, cannot change)")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
