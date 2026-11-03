# -*- coding: utf-8 -*-
r"""插入 `sec:epoch_sweep` 小节定义（修悬空 `\ref`）（2026-10-12）。

## 问题（我上一步的失误）

`tools/_p222` 的 `MON_NEW` 里写了 `Section~\ref{sec:epoch_sweep}`，
但同一脚本的**小节插入**因幂等检查（误判"已存在"）被跳过 →
**论文里只有 `\ref` 没有 `\label`** → 编译会给出 `LaTeX Warning: Reference
'sec:epoch_sweep' on page ... undefined`，正文渲染成 `??`。

## 修法

在 `\section{Discussion}` 之前插入该小节（含 `\label`），
并把 `tools/_p219` 的组内证据（n=30）写进去。

    python tools\_p229_insert_epoch_section.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

SEC = (
    "\\subsection{Within-dataset evidence: ten runs evaluated epoch by epoch}\n"
    "\\label{sec:epoch_sweep}\n\n"
    "Every comparison above pools runs drawn from different datasets, which makes the\n"
    "coefficient hard to read: $\\tau$ differs between datasets for reasons unrelated to the\n"
    "relation under test. To measure the relation where it is used---inside a single training\n"
    "trajectory---we evaluated all $100$ archived per-epoch checkpoints of ten runs (four\n"
    "datasets; $30$ checkpoints each for three of them and $10$ for the fourth; evaluation\n"
    "only, no retraining). Within each dataset the Kendall coefficient tracks zero-shot top-1\n"
    "at Spearman $+0.670$ (MS-COCO, $t=4.8$), $+0.970$ (DTD, $t=21.2$), $+0.915$ (Flickr30k)\n"
    "and $+0.397$ (Food-101, $t=2.3$): positive in all four, Fisher mean $+0.840$. The\n"
    "cleanest contrast is a single run, where only the training step varies: across epoch\n"
    "$1\\to10$ of one MS-COCO trajectory $\\tau_5$ falls $0.688\\to0.575$ while top-1 falls\n"
    "$60.14\\%\\to58.14\\%$, and the same monotone co-movement appears in all ten runs (mean\n"
    "Pearson $0.90$, $10/10$ positive; \\texttt{outputs/\\allowbreak a1\\_epoch\\_sweep.json}).\n\n"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()

    has_ref = "\\ref{sec:epoch_sweep}" in t
    has_label = "\\label{sec:epoch_sweep}" in t
    print(f"  \\ref{{sec:epoch_sweep}}: {'✅ 有' if has_ref else '无'}")
    print(f"  \\label{{sec:epoch_sweep}}: {'✅ 有' if has_label else '🔴 无'}")
    if has_label:
        print("  → 已有 label，无需插入")
        return 0

    anchor = "\\section{Discussion}"
    n = t.count(anchor)
    print(f"  锚点 \\section{{Discussion}}: 命中 {n}")
    if n != 1:
        return 1
    t2 = t.replace(anchor, SEC + anchor, 1)
    if not args.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p229")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = ("\\label{sec:epoch_sweep}" in t3 and "\\ref{sec:epoch_sweep}" in t3
          and "+0.840" in t3)
    print(f"\n  {'✅ 小节已插入（\ref 与 \label 都在）' if ok else '🔴 插入失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
