# -*- coding: utf-8 -*-
r"""Check whether either manuscript cites the specific runs whose labels are wrong.

The mislabelled runs live in outputs/route_c, outputs/route_d, outputs/route_e, outputs/siglip and
outputs/blip2. If a paper's numbers come from those directories, the exposure is direct; if they
come from elsewhere, the exposure is limited to how the method is named.

    python tools/_p788_exposure.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "lora_label_exposure.json"

SUSPECT_TREES = ["route_c", "route_d", "route_e", "siglip", "blip2", "theory/v1",
                 "theory/beta_pilot", "theory/adapter", "coco", "flickr30k"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}

    for label, d in (("Paper A", REPO / "paper合"), ("P3", REPO / "paper3" / "paper_ieee")):
        if not d.exists():
            continue
        print("=" * 104)
        print(f"{label}   ({d.relative_to(REPO)})")
        print("=" * 104)
        hits = {}
        for f in d.rglob("*.tex"):
            t = io.open(f, encoding="utf-8", errors="replace").read()
            for tree in SUSPECT_TREES:
                for m in re.finditer(r"[^.\n]{0,120}" + re.escape(tree) + r"[^.\n]{0,120}", t):
                    seg = " ".join(m.group(0).split())
                    if re.search(r"outputs/|\\\\texttt", seg):
                        hits.setdefault(tree, []).append({"file": str(f.relative_to(d)),
                                                          "text": seg[:200]})
        for tree in SUSPECT_TREES:
            n = len(hits.get(tree, []))
            if n:
                print(f"  {tree:<18} {n} mention(s) with a path")
                for h in hits[tree][:2]:
                    print(f"     [{h['file']}] {h['text'][:170]}")
        if not hits:
            print("  no direct path references to the suspect result trees")
        report[label] = {k: len(v) for k, v in hits.items()}
        print()

    print("=" * 104)
    print("reading")
    print("=" * 104)
    print("  A direct path reference means a number in the paper comes from a run whose 'LoRA'")
    print("  label is wrong, so that number has to be re-attributed or replaced.")
    print("  Otherwise the exposure is limited to how the method is named in prose and tables.")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
