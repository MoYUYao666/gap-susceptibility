# -*- coding: utf-8 -*-
r"""Find out what image and split sizes the existing COCO and Flickr runs actually used.

R2-3 objects that the study leans on Flickr30k and MS-COCO. The COCO retrieval numbers in the
paper are near-random with R@1 < 0.001, and R1-W4 asked the authors to verify the retrieval
protocol (gallery construction, directions, split, metric) before drawing cross-model conclusions.

Before running anything larger, establish the sample sizes the current runs used, so "larger" has a
concrete target and the existing numbers have a known protocol.

    python tools/_p749_protocol_sizes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 106)
    print("1. sample sizes recorded in the theory COCO / v1 trajectories")
    print("=" * 106)
    for rel in ("outputs/theory/coco/coco_both_r8/seed42/results.json",
                "outputs/theory/coco/coco_text_r8/seed42/results.json",
                "outputs/theory/coco/coco_full_ft/seed42/results.json",
                "outputs/theory/v1_trajectory/v1_both_r16/seed42/results.json"):
        p = PUB / rel
        if not p.exists():
            print(f"  missing {rel}")
            continue
        d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))

        def walk(o, path="$"):
            if isinstance(o, dict):
                for k, v in o.items():
                    yield from walk(v, f"{path}.{k}")
            elif isinstance(o, list):
                yield path, f"list[{len(o)}]"
            else:
                yield path, o

        print(f"  {rel}")
        for path, v in walk(d):
            if re.search(r"n_|num|size|samples|images|batch|epoch|split|test|train|val", path, re.I):
                print(f"     {path} = {v}")
        print()

    print("=" * 106)
    print("2. retrieval protocol in the experiment scripts")
    print("=" * 106)
    for rel in ("experiments/coco_experiments.py", "experiments/theory/coco_validation.py",
                "src/dataset.py", "src/config.py"):
        p = REPO / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        print(f"  {rel}  ({len(t.splitlines())} lines)")
        for m in re.finditer(r".{0,90}(n_images|num_images|max_samples|limit|subset|"
                             r"test_size|val_size|split|caption|gallery|R@1|top1|"
                             r"retrieval).{0,130}", t):
            seg = " ".join(m.group(0).split())
            print(f"     {seg[:200]}")
        print()

    print("=" * 106)
    print("3. what the paper says about the COCO protocol")
    print("=" * 106)
    for p in [REPO / "paper合" / "main_nc.tex"] + sorted((REPO / "paper合" / "sections").glob("*.tex")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"[^.]*\b(?:5?0?00 ?(?:images|pairs)|test set|gallery|"
                             r"near-random|MS-COCO|COCO val)\b[^.]*\.", t):
            seg = " ".join(m.group(0).split())
            if len(seg) > 50 and re.search(r"coco|gallery|near-random|test set", seg, re.I):
                ln = t[:m.start()].count("\n") + 1
                print(f"  {p.name}:{ln}")
                print(f"     {seg[:270]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
