# -*- coding: utf-8 -*-
r"""补完 `_p222` 的剩余 3 项（2026-10-12）。

| # | 待做 | 说明 |
|---|---|---|
| 3 | "four decimals" → "three decimals" | 上次未命中（可能措辞不同） |
| 5b | 组内 n=30 证据小节 | `sec:epoch_sweep` 已存在但内容待核 |
| 6 | `docs/A1_VENUE_DECISION.md` 过期更正 | 需写入 10-10 拒稿事实 |

**另补**：`highlights.tex` 第 2 条 "governs zero-shot robustness" 也应与正文一致（"tracks"）。

    python tools\_p227_finish_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"


def show(t: str, pat: str, w: int = 260, n: int = 2):
    ms = list(re.finditer(pat, t, re.S))
    print(f"    「{pat[:44]}」命中 {len(ms)}")
    for m in ms[:n]:
        s = " ".join(t[max(0, m.start() - 150):m.start() + w].split())
        print(f"      …{s[:380]}…")
    return len(ms)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0

    mt_p = A1 / "main.tex"
    mt = io.open(mt_p, encoding="utf-8", errors="replace").read()
    print("=" * 86)
    print("① 找 'decimals' 的实际措辞")
    print("=" * 86)
    show(mt, r"decimals")

    print()
    print("=" * 86)
    print("② 找 sec:epoch_sweep 小节内容")
    print("=" * 86)
    i = mt.find("sec:epoch_sweep")
    if i > 0:
        print("  " + " ".join(mt[i:i + 900].split())[:900])
    else:
        print("  🔴 无")

    print()
    print("=" * 86)
    print("③ 找 'governs' 在 abstract/highlights")
    print("=" * 86)
    for f in ("main.tex", "abstract.tex", "highlights.tex"):
        t = io.open(A1 / f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"govern", t, re.I):
            ln = t[:m.start()].count("\n") + 1
            print(f"  [{f}:{ln}] " + " ".join(
                t[max(0, m.start() - 90):m.start() + 110].split())[:200])

    print()
    print("=" * 86)
    print("④ docs/A1_VENUE_DECISION.md 尾部")
    print("=" * 86)
    vd = REPO / "docs" / "A1_VENUE_DECISION.md"
    if vd.exists():
        v = io.open(vd, encoding="utf-8", errors="replace").read()
        print(f"  文件 {len(v.splitlines())} 行；含 '2026-10-12 更正': "
              f"{'2026-10-12 更正' in v}")
        print("  末尾 300 字符: " + " ".join(v[-300:].split()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
