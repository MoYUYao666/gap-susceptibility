# -*- coding: utf-8 -*-
r"""把 `experiments.tex` 的细节块**手写锚点**移入 Supplementary（2026-10-13）。

## 为什么这次能成

前两次失败（`_p516`/`_p517`）都是**用正则扫 float 环境** ⇒ 环境不配平。
**这次：只用"手写的起止字符串"做整块文本替换，绝不触碰任何 `\begin/\end` 结构。**

## 移出清单（正文留结论句 + 关键数字）

| 块 | 现字符 | 正文留 | 依据 |
|---|---|---|---|
| 解码器 VLM（"A decoder VLM, and what does not replicate"） | ~1,900 | ~600 | R1.4/R3.13 的细节 |
| 下游检验（"A downstream check"） | ~2,100 | ~800 | R3.15/R3.16 的细节 |
| 操作点探针（"The probe measured at the paper's own operating point"） | ~1,700 | ~900 | R3.14/R3.23（**3.09× 必须留**） |
| Seed provenance | ~1,500 | ~400 | R3.17–R3.22 |
| 自适应基线 + 规则用途（合并） | ~2,100 | ~1,200 | R2.4/R3.9 |

    python tools\_p522_handwritten_moves.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
EX = PI / "sections" / "experiments.tex"
SUP = PI / "supplementary" / "supplementary.tex"

MOVES = [
    ("Decoder VLM",
     "\\textbf{A decoder VLM, and what does not replicate (Supplementary Section~S6).}",
     None,   # 用下面显式给出
     ),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    print(f"  experiments {len(t):,} 字符")
    # 先只**诊断**：把每块的起止锚点打印出来，人工确认后再改
    marks = [
        "\\textbf{A decoder VLM,",
        "\\textbf{A downstream check,",
        "\\textbf{The probe measured at the paper's own operating point.}",
        "\\textbf{Seed provenance and a numerical-environment control.}",
        "\\textbf{An adaptive baseline is better on this metric, and we say so.}",
        "\\textbf{What the rule is for.}",
        "\\textbf{Blank images are not a neutral probe.}",
        "\\textbf{What replicates.}",
        "\\textbf{Worst case rather than dispersion.}",
        "\\textbf{What we can and cannot say about the tail.}",
        "\\textbf{The Violation group as consistency evidence.}",
        "\\textbf{Result.}",
        "\\textbf{Theory} ($r = 4$):",
        "\\textbf{Random}:",
        "\\textbf{Violation}:",
        "\\subsection{Counterfactual Validation}",
        "\\subsection{Alignment Phase Transition}",
        "\\subsection{Setup}",
    ]
    pos = []
    for m in marks:
        i = t.find(m)
        pos.append((i if i >= 0 else 10 ** 9, m))
    pos.sort()
    print()
    print("  各块起始位置与长度：")
    for k, (i, m) in enumerate(pos):
        if i >= 10 ** 9:
            print(f"     🔴 未找到 {m}")
            continue
        nxt = pos[k + 1][0] if k + 1 < len(pos) and pos[k + 1][0] < 10 ** 9 else len(t)
        print(f"     L{t[:i].count(chr(10))+1:<5} {nxt - i:>7,} 字符 ｜ {m[:64]}")
    if not a.apply:
        print()
        print("  （预演 —— 本次只做诊断，不改文件）")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
