# -*- coding: utf-8 -*-
r"""把重算的 5-seed / batch-128 数字写进 `tab:position_strict`（2026-10-11）。

## 表体（4 行要改）

| 行 | 旧（3 seed 或未更新） | 新（5 seed，batch 128） |
|---|---|---|
| `OpenCLIP B/32 (LAION)` | $+0.0694$ / $+0.0881$ / $+0.0925$ | $+0.0802$ / $+0.0864$ / $+0.0996$ |
| `CLIP B/32$^\dagger$` | $-0.0288$ / $-0.0188$ / $+0.0127$ | $-0.0304$ / $-0.0204$ / $+0.0166$ |
| `CLIP B/16$^\dagger$` | $-0.0172$ / $+0.0107$ / $+0.0313$ | $-0.0166$ / $+0.0124$ / $+0.0376$ |

## 表注（两处）

1. **OpenCLIP 效应量**：旧写"$0.52$/$0.55$ of that spread … 排序 not resolved"→ **实为 $1.5$/$2.7$ sd，排序成立**；
2. **seed 口径**：旧写"$\dagger$ rows are three-seed means … archived rows use five seeds"
   → 现在**全部 5 seed**。

    python tools\_pa_strict_table_5seed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMP = REPO / "paper合" / "sections" / "empirical.tex"

ROWS = [
    # OpenCLIP 行
    (r"\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$",
     r"\mathbf{+0.0802}$ / $0.643$ & $+0.0864$ / $\mathbf{0.680}$ & $+0.0996$ / $0.672$"),
    # CLIP B/32† 行
    (r"\mathbf{-0.0288}$ / $0.621$ & $-0.0188$ / $0.679$ & $+0.0127$ / $0.670$",
     r"\mathbf{-0.0304}$ / $0.621$ & $-0.0204$ / $0.679$ & $+0.0166$ / $0.670$"),
    # CLIP B/16† 行
    (r"\mathbf{-0.0172}$ / $0.651$ & $+0.0107$ / $0.707$ & $+0.0313$ / $0.686$",
     r"\mathbf{-0.0166}$ / $0.651$ & $+0.0124$ / $0.707$ & $+0.0376$ / $0.686$"),
]

OLD_NOTE1 = (r"""The $\dagger$ rows are three-seed means
under the same protocol, as are the archived rows, which use five seeds; on CLIP B/32 the seed-to-seed
standard deviation is $0.001$--$0.002$, so the gaps those arms separate are several times that spread. On
OpenCLIP the differences between adjacent arms are the smallest of any backbone here: against
the per-arm seed-to-seed standard deviation of $0.012$--$0.014$ they amount to $0.52$ and $0.55$ of that spread, so the
arm ordering on this backbone is not resolved and we do not rest any conclusion on it. The
three-seed means themselves are $+0.066$, $+0.075$ and $+0.086$ for text-only, both-position and
vision-only respectively.""")

NEW_NOTE1 = (r"""Every row is a five-seed mean under the
same protocol, at batch $128$ throughout, and the seed-to-seed standard deviation is
$0.0006$--$0.006$ depending on the backbone, so the separations the arms rest on are one to several times
that spread. On OpenCLIP, the backbone with the smallest relative separations, the adjacent arms differ by
$1.5$ and $2.7$ pooled standard deviations, so its ordering is resolved and agrees with the other
contrastive backbones. The five-seed means are $+0.0802$, $+0.0864$ and $+0.0996$ for text-only,
both-position and vision-only respectively.""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EMP, encoding="utf-8", errors="replace").read()

    print("=== 表体 3 行 ===")
    n = 0
    for old, new in ROWS:
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠️'} 命中 {c}: {old[:56]}…")
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
    print(f"  → {n}/3")

    print("\n=== 表注 ===")
    c2 = t.count(OLD_NOTE1)
    print(f"  命中 {c2}")
    if c2 == 1:
        t = t.replace(OLD_NOTE1, NEW_NOTE1, 1)
        print("  ✅ 已改（全部 5 seed + batch 128 + OpenCLIP 1.5/2.7 sd）")

    if not a.apply:
        print("\n  （预演）")
        return 0
    bak = EMP.with_suffix(".tex.bak_5seed")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(EMP, encoding="utf-8").read())
    io.open(EMP, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(EMP, encoding="utf-8", errors="replace").read()
    for k in (r"$+0.0802$", r"$-0.0304$", r"$-0.0166$", r"$1.5$ and $2.7$ pooled",
              "Every row is a five-seed mean"):
        assert k in t2, f"断言失败：缺 {k}"
    for k in (r"$+0.0694$", r"$-0.0288$", r"$-0.0172$", "three-seed means"):
        assert k not in t2, f"旧内容仍在: {k}"
    print("  ✅ tab:position_strict 已更新（3 行 + 表注）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
