# -*- coding: utf-8 -*-
r"""清除 `k = 0.043` 的**全部残留**（图注 + 引言 + 理论），2026-10-04。

## 背景

`k=0.043` 已确认**无法复现**（线性拟合给 0.257），且**斜率本身不应报**
（相邻区间局部斜率 −0.20/+0.89/−0.35/+1.39/−0.40 **正负交替** → 无可辨趋势）。
正确陈述：**区间 12.75–14.09（10%）vs $\sqrt r$ 预测 8 倍**。

`tools/_pa_fix_k_slope.py` 只改了正文两处；本脚本清掉剩余 **4 处**（含 2 处图注）。

## 注意

`empirical.tex:77` 的 `$-0.043$` 是 **MS-COCO 的 rank-8 数值**，**不是 k**，**不动**。

    python tools\_pa_fix_k_slope2.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

FLAT = (r"restricted to a $10\%$ band across $r\in[1,64]$ (means $12.75$--$14.09$ over five seeds per rank), "
        r"where $\|g_v\|\propto\sqrt{r}$ would predict an eightfold change")

EDITS = [
    (S / "validation.tex",
     r"\caption{Effective Rank Saturation. $\|g_v\|$ is flat across $r \in [1,64]$ ($k=0.043$), falsifying the $\sqrt{r}$ scaling prediction.",
     r"\caption{Effective Rank Saturation. $\|g_v\|$ stays within a $10\%$ band across $r \in [1,64]$, "
     r"falsifying the $\sqrt{r}$ scaling prediction."),
    (S / "supplement.tex",
     r"\caption{Falsification of $\sqrt{r}$ scaling. Red: random projection. Blue: actual $\|g_v\|$ ($k=0.043$).}",
     r"\caption{Falsification of $\sqrt{r}$ scaling. Red: random projection. Blue: actual $\|g_v\|$, "
     r"which stays within $10\%$ across $r\in[1,64]$ against the eightfold change $\sqrt{r}$ predicts.}"),
    (S / "introduction.tex",
     r"is falsified by experiment ($\|g_v\|$ is flat across ranks, $k=0.043$)",
     r"is falsified by experiment ($\|g_v\|$ varies by only $10\%$ across $r\in[1,64]$, "
     r"where $\sqrt{r}$ predicts an eightfold change)"),
    (S / "theory.tex",
     r"$\|g_v\|$ is nearly flat across $r \in [1,64]$ ($k=0.043$).",
     r"$\|g_v\|$ varies by only $10\%$ across $r \in [1,64]$ ($12.75$--$14.09$)."),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for p, old, new in EDITS:
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {p.name}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        else:
            print(f"  ⚠ {p.name}：未唯一命中（{c} 次）")
    if apply:
        left = []
        for f in list(S.glob("*.tex")) + [REPO / "paper合" / "main_nc.tex",
                                          REPO / "paper合" / "main_springer.tex"]:
            if not f.exists():
                continue
            tt = io.open(f, encoding="utf-8").read()
            for m in __import__("re").finditer(r"k\s*=\s*0\.043", tt):
                left.append(f.name)
        print(f"\n  {'✅' if not left else '⚠'} 残留 'k=0.043': {len(left)} 处 {left}")
        assert not left, "仍有残留"
        # 确认 MS-COCO 的 -0.043 未被误伤
        e = io.open(S / "empirical.tex", encoding="utf-8").read()
        assert "rank-8 $-0.043$" in e, "误伤了 MS-COCO 的 -0.043"
        print("  ✅ 已确认未误伤 MS-COCO 的 $-0.043$")
    else:
        print(f"\n  {n}/{len(EDITS)} 处可改（预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
