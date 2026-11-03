# -*- coding: utf-8 -*-
r"""Rewrite the COCO and LoRA wording in Paper A and P3 from the corrected runs.

Two defects are being repaired at once:

  1. the retrieval metric double counted, so every image-to-text figure recorded during the scale-up
     was wrong (R@1 exceeded 1, which is impossible); the corrected evaluator is in
     tools/_p754_coco_scaleup.py
  2. apply_lora_to_model never froze the base model, so every run labelled "LoRA rank r" trained the
     whole adapted tower - 145,170,177 parameters of which 196,608 were LoRA; the fix is in
     src/lora.py and the reruns use seeds 42/123/456

Both papers are rewritten to describe what was actually run, with the corrected numbers read from
outputs/analysis/coco_scaleup.json rather than typed in.

    python tools/_p789_update_papers.py [--dry-run | --apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCALE = REPO / "outputs" / "analysis" / "coco_scaleup.json"
PA = REPO / "paper合"
P3 = REPO / "paper3" / "paper_ieee"


def load_summary():
    d = json.loads(SCALE.read_text(encoding="utf-8", errors="ignore"))
    runs = d["runs"]
    out = {}
    for arm in ("frozen", "text_only", "both"):
        rs = [r for r in runs if r["arm"] == arm]
        if not rs:
            continue
        def m(k):
            v = [r[k] for r in rs if r.get(k) is not None]
            return st.mean(v), (st.stdev(v) if len(v) > 1 else 0.0)
        out[arm] = {"n": len(rs),
                    **{k: m(k) for k in ("R@1", "R@5", "R@10", "R@1_i2t", "R@1_t2i")}}
    return d, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        a.dry_run = True

    d, summ = load_summary()
    print("=" * 104)
    print("corrected scale-up (COCO train2014 10,000 images -> val2014 3,000 images)")
    print("=" * 104)
    print(f"  config: {json.dumps(d['config'], ensure_ascii=False)}")
    print()
    print(f"  {'arm':<12} {'n':>2} {'R@1':>14} {'i2t R@1':>14} {'t2i R@1':>14}")
    for arm, s in summ.items():
        print(f"  {arm:<12} {s['n']:>2} "
              f"{s['R@1'][0]:>7.4f}±{s['R@1'][1]:.4f} "
              f"{s['R@1_i2t'][0]:>7.4f}±{s['R@1_i2t'][1]:.4f} "
              f"{s['R@1_t2i'][0]:>7.4f}±{s['R@1_t2i'][1]:.4f}")
    if "text_only" in summ and "both" in summ:
        t, b = summ["text_only"]["R@1"][0], summ["both"]["R@1"][0]
        print()
        print(f"  both - text_only on R@1: {b - t:+.4f}")
        print(f"  frozen -> text_only     : {summ['text_only']['R@1'][0] - summ['frozen']['R@1'][0]:+.4f}")
    print()

    print("=" * 104)
    print("what each paper needs")
    print("=" * 104)
    for label, root in (("Paper A", PA), ("P3", P3)):
        if not root.exists():
            continue
        files = [p for p in root.rglob("*.tex")]
        lora = sum(len(re.findall(r"LoRA", io.open(p, encoding="utf-8", errors="replace").read()))
                   for p in files)
        coco = sum(len(re.findall(r"COCO", io.open(p, encoding="utf-8", errors="replace").read()))
                   for p in files)
        print(f"  {label:<9} {len(files):>3} .tex files   LoRA {lora:>4} mentions   COCO {coco:>4}")
    print()
    print("  Paper A : replace the COCO retrieval statement and the method naming")
    print("  P3      : replace the method naming; its submitted PDF cannot change, so the fix")
    print("            applies to the sources and to any later revision")
    if a.dry_run:
        print()
        print("  (dry run; nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
