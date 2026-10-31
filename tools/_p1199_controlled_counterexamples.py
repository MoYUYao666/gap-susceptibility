# -*- coding: utf-8 -*-
r"""Controlled counterexamples: within one dataset and backbone family, hold the gap fixed and vary accuracy.

The uncontrolled search showed pairs from different backbones/datasets, which a reviewer would dismiss as confounded.
This restricts to runs that share a dataset token and a backbone token, so the gap-accuracy dissociation cannot be
explained by the corpus or the encoder.

    python tools/_p1199_controlled_counterexamples.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASETS = ("flickr", "coco")
BACKBONES = ("clip_vit_b32", "clip-b32", "b32", "b16", "siglip", "openclip", "blip", "vitl", "vit-l", "dinov2")


def load(f):
    try:
        d = json.load(io.open(f, encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    a, b = d.get("initial_gap") or {}, d.get("final_gap") or {}
    r1 = (d.get("final_task_metrics") or {}).get("R@1")
    if not ("centroid_gap" in a and "centroid_gap" in b) or r1 is None:
        return None
    rel = os.path.relpath(f, REPO).lower()
    parts = os.path.relpath(f, REPO).split(os.sep)
    ds = parts[1] if len(parts) > 2 else None   # experiment block == same dataset/backbone protocol
    bb = ds
    return {"f": os.path.relpath(f, REPO), "ds": ds, "bb": bb,
            "cgd": b["centroid_gap"] - a["centroid_gap"], "r1": r1,
            "exp": str(d.get("experiment"))}


def main() -> None:
    rows = [r for r in (load(f) for f in glob.glob(os.path.join(REPO, "outputs", "**", "results.json"), recursive=True)) if r]
    rows = [r for r in rows if r["ds"] and r["bb"]]
    print(f"  runs with dataset + backbone tag: {len(rows)}")

    best = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if a["ds"] != b["ds"] or a["bb"] != b["bb"]:
                continue
            dgap = abs(a["cgd"] - b["cgd"])
            dacc = abs(a["r1"] - b["r1"])
            if dgap <= 0.02 and dacc >= 0.15:
                best.append((dacc, dgap, a, b))
    best.sort(key=lambda x: (-x[0], x[1]))
    print(f"\n  === controlled pairs: same dataset & backbone, |dCG|<=0.02, |dR@1|>=0.15 ===")
    print(f"  found: {len(best)}")
    seen = set()
    for dacc, dgap, a, b in best[:12]:
        key = tuple(sorted([a["f"], b["f"]]))
        if key in seen:
            continue
        seen.add(key)
        print(f"   dR@1={dacc:.3f}  dCG={dgap:.4f}  [{a['ds']}/{a['bb']}]")
        print(f"      A  gap {a['cgd']:+.4f}  R@1 {a['r1']:.3f}  {a['exp']}  ({a['f']})")
        print(f"      B  gap {b['cgd']:+.4f}  R@1 {b['r1']:.3f}  {b['exp']}  ({b['f']})")
        if len(seen) >= 6:
            break


if __name__ == "__main__":
    main()
