# -*- coding: utf-8 -*-
r"""修正零样本段的"within 0.8 pp"（重绘 `fig12` 时断言捕获，2026-10-05）。

## 问题

**正文**（`empirical.tex:133` 与 `:138` 图注）：

> "on DTD and Food101 both fine-tuned variants stay within **$0.8$ percentage points** of the frozen
> baseline"

**源数据**（`outputs/zeroshot_extra.json`）：

| 数据集 | 变体 | 值 | Frozen | 偏差 |
|---|---|---|---|---|
| DTD | Text-only | 43.33 | 43.27 | +0.06 |
| DTD | Both | 42.53 | 43.27 | +0.74 |
| Food101 | Text-only | 80.67 | 80.60 | +0.07 |
| **Food101** | **Both** | **79.73** | 80.60 | **+0.87** ← **超 0.8** |

**最大偏差 0.87 pp > 0.8** → 主张不成立。

## 改法

不改成"0.9"了事，而是**分变体如实陈述**——这同时暴露一个更细的差别：
**text-only 的偏差（≤0.07）比 both-position（≤0.87）小一个数量级**，
与本文"文本侧适配更保对齐"的主线**一致**。

## 发现方式

`tools/_pa_rebuild_fig12.py` 在**画图前先断言正文主张**，故在重绘时立即暴露。
（若无此断言，重绘只会悄悄产出一张与正文不符的图。）

    python tools\_pa_fix_zeroshot_claim.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD_TEXT = ("on DTD and Food101 both fine-tuned variants stay within $0.8$ percentage points of the frozen "
            "baseline, while on ImageNet full fine-tuning collapses.")
NEW_TEXT = ("on DTD and Food101 the text-only arm stays within $0.1$ percentage points of the frozen "
            "baseline while the both-position arm stays within $0.9$, and on ImageNet full fine-tuning "
            "collapses.")

OLD_CAP = ("All fine-tuned variants stay within 0.8 percentage points of the frozen baseline.")
NEW_CAP = ("The text-only arm stays within 0.1 percentage points of the frozen baseline and the "
           "both-position arm within 0.9.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_TEXT, NEW_TEXT, "正文句"), (OLD_CAP, NEW_CAP, "图注")):
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ {why}：命中 {c} 次")
    if apply and n == 2:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "within 0.8 percentage" not in t2 and "within $0.8$ percentage" not in t2
        assert "within $0.1$ percentage" in t2 and "within $0.9$" in t2
        print("  ✅ 已改并断言通过（0.8 pp 主张已消除）")
    else:
        print(f"\n  {n}/2 处{'已改' if apply else '可改'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
