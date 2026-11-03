# -*- coding: utf-8 -*-
r"""同步 `discussion.tex` 的 VLM 数字到 **13 seed**（2026-10-11）。

    python tools\_pa_disc_vlm13.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

PAIRS = [
    (r"reducing $DG^*$ by $15.8\pm10.4\%$ against $67.4\pm7.3\%$ for text-only and $86.5\pm8.1\%$ for both positions over five seeds",
     r"reducing $DG^*$ by $18.0\pm8.8\%$ against $66.5\pm8.3\%$ for text-only and $87.9\pm5.3\%$ for both positions over thirteen seeds"),
    (r"their seed ranges overlap completely ($73.1$--$95.1\%$ against $59.4$--$76.3\%$) and they differ by $0.62$ pooled standard deviations",
     r"their seed ranges overlap ($73.1$--$95.1\%$ against $47.8$--$78.8\%$) and they differ by $0.86$ pooled standard deviations"),
    (r"and the both-position reduction ranges from $73.1\%$ to $95.1\%$ across three seeds against $59.4\%$ to $71.1\%$ for text-only.",
     r"and the both-position reduction ranges from $73.1\%$ to $95.1\%$ across thirteen seeds against $47.8\%$ to $78.8\%$ for text-only."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    print("=== 锚点 ===")
    n_ok = 0
    for old, new in PAIRS:
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠️'} 命中 {c}: {old[:60]}…")
        if c == 1:
            t = t.replace(old, new, 1)
            n_ok += 1
    print(f"  → {n_ok}/{len(PAIRS)}")

    # 兜底：替换剩余的三 seed / 五 seed 措辞（仅限 VLM 上下文）
    t2 = t.replace("across three seeds against", "across thirteen seeds against")

    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_vlm13")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in (r"$18.0\pm8.8\%$", r"$66.5\pm8.3\%$", r"$87.9\pm5.3\%$",
              "thirteen seeds", r"$47.8$--$78.8$", "0.86"):
        assert k in t3, f"断言失败：缺 {k}"
    assert r"$15.8\pm10.4\%$" not in t3, "旧 5-seed 数字仍在"
    print("  ✅ discussion.tex 已同步 13-seed 数字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
