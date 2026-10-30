# -*- coding: utf-8 -*-
r"""Trace how the retrieval evaluation builds its loader, to fix the metric at the right place.

The training loss is correct: within a batch, sample i's image pairs with sample i's caption, so the
diagonal is the positive. The retrieval metric is not: it flattens the whole loader into an (N, N)
matrix and still treats the diagonal as positive, but row i and column i are no longer the same
pair once images repeat across caption rows.

This inspects the trainer's evaluation path and the COCO loader so the fix is made where the
alignment information is still available.

    python tools/_p752_trace_eval.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = (REPO / "src" / "trainer.py").read_text(encoding="utf-8", errors="ignore")

    print("=" * 104)
    print("1. every place the trainer asks for retrieval metrics")
    print("=" * 104)
    for m in re.finditer(r".{0,200}_compute_retrieval_metrics\(.{0,160}", t, re.S):
        ln = t[:m.start()].count("\n") + 1
        print(f"  L{ln}: {' '.join(m.group(0).split())[:300]}")

    print()
    print("=" * 104)
    print("2. does the dataset expose an image identifier?")
    print("=" * 104)
    d = (REPO / "src" / "dataset.py").read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r".{0,120}(image_id|image_file|file_name|image_path).{0,160}", d, re.S):
        ln = d[:m.start()].count("\n") + 1
        seg = " ".join(m.group(0).split())
        print(f"  L{ln}: {seg[:260]}")

    print()
    print("=" * 104)
    print("3. the __getitem__ payloads (train vs val)")
    print("=" * 104)
    for m in re.finditer(r"def __getitem__.*?(?=\n    def |\Z)", d, re.S):
        seg = m.group(0)
        ln = d[:m.start()].count("\n") + 1
        print(f"  L{ln}: {' '.join(seg.split())[:400]}")
        print()

    print("=" * 104)
    print("4. how evaluation loaders are constructed in the theory scripts")
    print("=" * 104)
    for rel in ("experiments/theory/coco_validation.py",):
        p = REPO / rel
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r".{0,140}(DataLoader|test_loader|val_loader|max_samples|split=)"
                             r".{0,200}", s, re.S):
            ln = s[:m.start()].count("\n") + 1
            print(f"  {rel}:{ln}  {' '.join(m.group(0).split())[:260]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
