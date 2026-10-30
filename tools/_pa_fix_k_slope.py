# -*- coding: utf-8 -*-
r"""把 $k=0.043$ 的表述改掉（**等实验跑完后再应用**）。

## 依据（`docs/K043_INVESTIGATION.md` 最终结论）

重测（both 臂，严格冻结，3 seeds/rank，覆盖 $r\in[1,64]$）：

| rank | 1 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|
| $\|g_v\|$ | 13.037 | 12.754 | 13.369 | 13.127 | 14.093 | 13.815 |

- **平坦成立且裕度极大**：极差 **10%**，而 $\sqrt r$ 预测应变化 **8 倍** → 实测比预测小约 **80 倍**；
- **$k=0.043$ 无法复现**：线性拟合得 0.257；
- **斜率本身不应报**：相邻区间局部斜率 **−0.20 / +0.89 / −0.35 / +1.39 / −0.40**，
  **正负交替** → 无可辨趋势，任何斜率都是噪声残差。

## 因此改为

| 原 | 新 |
|---|---|
| "$\|g_v\|$ is nearly flat across $r\in[1,64]$, with slope $k=0.043$" | "$\|g_v\|$ varies by only 10% across $r\in[1,64]$ (12.75–14.09), where $\sqrt r$ would predict an eightfold change" |

**理由**：报一个来自无趋势曲线的斜率，是把噪声当信号；报区间与预测的对比直接、可复核、更有说服力。

    python tools\_pa_fix_k_slope.py            # 预演
    python tools\_pa_fix_k_slope.py --apply    # 应用
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS = [
    (S / "validation.tex",
     "nearly flat across $r \\in [1,64]$, with slope $k = 0.043$",
     "restricted to a $10\\%$ band across $r \\in [1,64]$ (means $12.75$--$14.09$ over five seeds per rank), "
     "where $\\|g_v\\| \\propto \\sqrt{r}$ would predict an eightfold change"),
    (S / "supplement.tex",
     "$R^2=0.96$) vs.\\ actual $\\|g_v\\|$ ($k=0.043$)",
     "$R^2=0.96$) vs.\\ actual $\\|g_v\\|$ (flat to within $10\\%$ across $r\\in[1,64]$, "
     "against the eightfold change $\\sqrt{r}$ predicts)"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for p, old, new in EDITS:
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {p.name}：命中")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        else:
            print(f"  ⚠ {p.name}：未唯一命中（{c} 次）")
            # 打印实际文本以便修正匹配串
            i = t.find("flat across")
            if i > 0:
                print("     实际: …" + t[i:i + 120].replace("\n", " ") + "…")
    if apply and n:
        left = 0
        for f in list(S.glob("*.tex")) + [REPO / "paper合" / "main_nc.tex",
                                          REPO / "paper合" / "main_springer.tex"]:
            if f.exists():
                left += io.open(f, encoding="utf-8").read().count("k = 0.043") \
                    + io.open(f, encoding="utf-8").read().count("k=0.043")
        print(f"\n  {'✅' if left == 0 else '⚠'} 全文残留 '0.043': {left} 处")
    else:
        print(f"\n  {n}/{len(EDITS)} 处可改（预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
