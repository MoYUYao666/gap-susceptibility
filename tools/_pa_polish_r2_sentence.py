# -*- coding: utf-8 -*-
r"""把上一轮替换产生的嵌套括号改写通顺（2026-10-02）。

上一轮把 `mean $R^2 > 0.96$` 批量替换为带括注的长句，结果出现嵌套括号：

- 图注：`(mean $R^2 = 0.985$ over the LoRA configurations (the full-fine-tuning pilot is lower, at $0.922$, and is reported separately below))`
- 正文：`mean $R^2 = 0.985$ over the LoRA configurations (…) across PEFT configurations, …`（语序断裂）

本脚本改为两句干净表述：主句给 LoRA 数值，另起一句给 full_ft 的边界。

    python tools\_pa_polish_r2_sentence.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

PAIRS = [
    # 图注
    ("All PEFT configurations exhibit clean exponential convergence (mean $R^2 = 0.985$ over the LoRA "
     "configurations (the full-fine-tuning pilot is lower, at $0.922$, and is reported separately below)).",
     "All PEFT configurations exhibit clean exponential convergence: the LoRA arms fit at mean $R^2 = 0.986$ "
     "(range $0.978$--$0.997$), while the full-fine-tuning pilot is lower at $0.922$."),
    # 正文
    ("The ODE achieves mean $R^2 = 0.985$ over the LoRA configurations (the full-fine-tuning pilot is lower, "
     "at $0.922$, and is reported separately below) across PEFT configurations, outperforming",
     "Across PEFT configurations the ODE achieves mean $R^2 = 0.986$ over the LoRA arms (range "
     "$0.978$--$0.997$; the full-fine-tuning pilot fits at $0.922$, and we return to it below), "
     "outperforming"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new in PAIRS:
        c = t.count(old)
        if c == 1:
            print("  ✅ 命中一处嵌套括号表述")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ 未命中（出现 {c} 次）：{old[:70]}…")
    if apply and n:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "and is reported separately below" not in t2, "断言失败：旧括注仍在"
        # 数值与实测一致（LoRA n=6: mean 0.9855, min 0.9777, max 0.9965）
        assert "0.986" in t2 and "0.978" in t2 and "0.997" in t2
        print("  ✅ 已改并断言通过")
    else:
        print(f"  {n}/{len(PAIRS)} 处{'已改' if apply else '可改'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
