# -*- coding: utf-8 -*-
r"""扫描 paper合 里 VLM 与严格冻结的**旧数字残留**（2026-10-11）。

    python tools\_p178_scan_stale_numbers.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (旧值片段, 说明)
STALE = [
    ("15.8\\pm10.4", "VLM vision_only 5-seed"),
    ("67.4\\pm7.3", "VLM text_only 5-seed"),
    ("86.5\\pm8.1", "VLM both 5-seed"),
    ("12.4\\pm4.7", "VLM vision_only 3-seed"),
    ("66.8\\pm6.5", "VLM text_only 3-seed"),
    ("85.2\\pm11.2", "VLM both 3-seed"),
    ("+0.0694", "OpenCLIP text_only 旧"),
    ("+0.0881", "OpenCLIP both 旧"),
    ("+0.0925", "OpenCLIP vision_only 旧"),
    ("-0.0288", "CLIP B/32 text_only 3-seed"),
    ("-0.0188", "CLIP B/32 both 3-seed"),
    ("-0.0172", "CLIP B/16 text_only 3-seed"),
    ("+0.0107", "CLIP B/16 both 3-seed"),
    ("+0.0313", "CLIP B/16 vision_only 3-seed"),
    ("-0.0488", "COCO r2 batch64"),
    ("-0.0944", "COCO r8 batch64"),
    ("-0.1315", "COCO r32 batch64"),
    ("-0.1396", "COCO r64 batch64"),
    ("0.52$ and $0.55", "OpenCLIP 效应量 旧"),
    ("three-seed means", "seed 口径 旧"),
    ("five seeds, small", "VLM 段 旧"),
]


def main() -> int:
    total = 0
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        hits = []
        for pat, tag in STALE:
            for m in re.finditer(re.escape(pat), t):
                s = " ".join(t[max(0, m.start() - 110):m.start() + 130].split())
                hits.append((tag, pat, s))
        if hits:
            print(f"\n{'=' * 78}\n{Path(f).name} ｜ {len(hits)} 处\n{'=' * 78}")
            for tag, pat, s in hits:
                print(f"  ⚠️ [{tag}] `{pat}`")
                print(f"      …{s[:230]}…")
            total += len(hits)
    print(f"\n{'=' * 78}")
    print(f"旧数字残留总计: {total}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
