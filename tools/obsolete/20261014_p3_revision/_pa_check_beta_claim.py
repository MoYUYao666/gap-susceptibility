# -*- coding: utf-8 -*-
r"""核对补充材料里 beta_theor 那句的算术，以及 tab:coco_ode 的拟合 beta 范围。

背景：全稿数字溯源扫描（204 个唯一小数）只发现 2 个不在 outputs 中，其中
`\beta_{\text{theor}} \approx 0.0035` 是理论量级说明。该句称"roughly 40× smaller than the fitted
values (\beta \approx 0.14--0.16)"——**比值必须与所给范围自洽**，否则是可被审稿人当场抓住的算术错误。

    python tools\_pa_check_beta_claim.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"

BT = 0.0035
CLAIMED_RANGE = (0.14, 0.16)
CLAIMED_FACTOR = 40


def main() -> int:
    print('=== ① 句内自洽性：fitted / beta_theor 与「roughly 40x」是否相符 ===')
    lo, hi = CLAIMED_RANGE[0] / BT, CLAIMED_RANGE[1] / BT
    print(f"  给定范围 {CLAIMED_RANGE} 与 beta_theor={BT}")
    print(f"  比值区间 = {lo:.0f}x – {hi:.0f}x  （句称 roughly {CLAIMED_FACTOR}x）")
    ok = lo <= CLAIMED_FACTOR <= hi or abs((lo + hi) / 2 - CLAIMED_FACTOR) <= 5
    print(f"  → {'✅ 自洽（40 落在范围内/附近）' if ok else '❌ 不自洽'}")

    print("\n=== ② 与 tab:coco_ode 实际拟合 beta 的对照 ===")
    t = io.open(SUP, encoding="utf-8").read()
    i = t.find("tab:coco_ode")
    seg = t[max(0, i - 200):i + 2200]
    # 形如 & $0.093 \pm 0.035$  或  & 0.093 \pm 0.035
    vals = []
    for m in re.finditer(r"&\s*\$?([0-9]*\.?[0-9]+)\s*\\pm", seg):
        v = float(m.group(1))
        if 0.0 < v < 1.0:
            vals.append(v)
    if vals:
        lo2, hi2 = min(vals), max(vals)
        print(f"  表内解析到 {len(vals)} 个带 ± 的值，范围 {lo2:.3f} – {hi2:.3f}")
        print(f"  与 beta_theor 的比值：{lo2 / BT:.0f}x – {hi2 / BT:.0f}x")
        print(f"  → 文中写的 fitted 范围 0.14–0.16："
              f"{'在表内范围内 ✅' if lo2 <= 0.14 and 0.16 <= hi2 else '需人工确认 ⚠️'}")
    else:
        print("  未解析到拟合值，需人工确认")

    print("\n=== ③ 该段的诚实性（是否已承认理论不完善）===")
    j = t.find("beta_{\\text{theor}}")
    ctx = t[j:j + 700].replace("\n", " ")
    honest = ("additional modeling" in ctx) or ("requires" in ctx)
    print(f"  含'需要额外建模'类表述：{'✅ 是' if honest else '❌ 否'}")
    print("  片段: " + ctx[:330])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
