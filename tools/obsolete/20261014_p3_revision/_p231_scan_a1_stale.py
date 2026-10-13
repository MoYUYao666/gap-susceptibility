# -*- coding: utf-8 -*-
r"""扫 A1 全套投稿件的旧主张残留（2026-10-12）。

新标题：*Order Preservation **Tracks** Zero-Shot Accuracy under Classification Fine-Tuning*
旧标题：*Order Preservation as a **Zero-Overhead Monitor** for Classification Fine-Tuning*

    python tools\_p231_scan_a1_stale.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"

STALE = [
    ("Zero-Overhead Monitor", "旧标题"),
    ("zero-overhead training-time monitor", "旧卖点"),
    ("Zero-overhead", "旧标题（大小写）"),
    ("Only the second governs", "与 Table 1 冲突"),
    ("matches measurement to four decimals", "位数错"),
    ("matches measurements with r = 1.000", "r=1.000 未限定"),
    ("monitor for classification-oriented fine-tuning", "监控器主张"),
    ("Neurocomputing", "旧目标刊"),
    ("244 words", "旧词数"),
    ("238 words", "旧词数"),
    ("49 pages", "旧页数"),
    ("patch size", "旧归因"),
]


def main() -> int:
    print("=" * 90)
    print("扫描 A1/*.tex（含备份文件排除）")
    print("=" * 90)
    files = [f for f in sorted(glob.glob(str(A1 / "*.tex")))
             if ".bak" not in f]
    total = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        hits = []
        for pat, tag in STALE:
            n = t.count(pat)
            if n:
                hits.append((tag, pat, n))
        if hits:
            print(f"\n  🔴 {Path(f).name}")
            for tag, pat, n in hits:
                print(f"       [{tag}] `{pat}` × {n}")
                for m in list(re.finditer(re.escape(pat), t))[:2]:
                    ln = t[:m.start()].count("\n") + 1
                    s = " ".join(t[max(0, m.start() - 100):m.start() + 140].split())
                    print(f"         L{ln}: …{s[:230]}…")
            total += len(hits)
        else:
            print(f"  ✅ {Path(f).name}")
    print()
    print("=" * 90)
    print(f"残留总计: {total}")
    print("=" * 90)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
