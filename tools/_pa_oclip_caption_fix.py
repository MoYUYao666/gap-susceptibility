# -*- coding: utf-8 -*-
r"""修正表注里 OpenCLIP 的效应量说法（2026-10-10）。

## 我先前写的（错）

> *"On OpenCLIP the gap between adjacent arms is the smallest of any backbone here,
> **at about twice the archived seed-to-seed deviation**, and its ordering should be
> read with that in mind."*

**"twice" 是错的。** 那个说法用了**错误的参照量**
（拿 CLIP B/32 r8 的跨臂 sd = 0.0030 当分母）。

## 按**逐臂 sd** 重算（`tools/_p92_oclip_effectsize.py`，OpenCLIP 现已 3 seed）

| 相邻臂 | \|Δmean\| | 合并 sd | 效应量 |
|---|---|---|---|
| `text_only` vs `both` | 0.0092 | 0.0175 | **0.52 sd** |
| `both` vs `vision_only` | 0.0105 | 0.0192 | **0.55 sd** |
| `text_only` vs `vision_only` | 0.0197 | 0.0186 | 1.05 sd |

**→ 相邻臂差异**小于一个 sd**（0.52 / 0.55），**统计上不成立**。

## 改动

**把"2×"改为实测量化**，并明确写"相邻臂差异小于一个 seed-to-seed sd，
故 OpenCLIP 上的臂排序不应被解读为已建立"。

    python tools\_pa_oclip_caption_fix.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = ("On\nOpenCLIP the gap between adjacent arms is the smallest of any backbone here, "
       "at about twice the archived\nseed-to-seed deviation, and its ordering should be "
       "read with that in mind.")

NEW = ("On\nOpenCLIP the differences between adjacent arms are the smallest of any "
       "backbone here: against\nthe per-arm seed-to-seed standard deviation of "
       "$0.012$--$0.014$ they amount to $0.52$ and $0.55$ of that spread, so the\n"
       "arm ordering on this backbone is not resolved and we do not rest any conclusion "
       "on it. The\nthree-seed means themselves are $+0.066$, $+0.075$ and $+0.086$ for "
       "text-only, both-position and\nvision-only respectively.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "0.52$ and $0.55" in t:
        print("  已改，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD)}）")
        # 打印实际文本以便对齐
        i = t.find("On OpenCLIP")
        if i < 0:
            i = t.find("OpenCLIP the gap")
        if i >= 0:
            print("  实际文本 repr:")
            print("   ", repr(t[max(0, i - 40):i + 300]))
        return 1
    t = t.replace(OLD, NEW, 1)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "0.52$ and $0.55" in t2 and "twice the archived" not in t2
    print("  ✅ 表注已修正：'2×' → 实测 0.52/0.55 sd，并写明排序未被解析")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
