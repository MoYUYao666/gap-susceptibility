# -*- coding: utf-8 -*-
r"""为 Paper A 生成 Highlights（Neurocomputing 要求 3–5 条，每条 ≤85 字符）。

## 依据

`_guide_neurocomputing.txt`：「Highlights should consist of 3 to 5 …」（与 Elsevier 通行一致）。
本稿此前**从未投稿**，故无 highlights 与 cover letter —— 本次新建。

## 内容来源（全部已核）

| 条 | 依据 |
|---|---|
| 1 | 相关性改口径后 **n=204, DG r=−0.714 vs CG r=−0.594**（`outputs/analysis/dg_r1_reproducible.json`） |
| 2 | ODE 拟合 **中位 R² 0.9718**（`tools/_pa_verify_core_claims.py` 复核 13 处 R²） |
| 3 | 严格冻结 5 seeds：**text-only −0.0465 vs both −0.0258**（CLIP） |
| 4 | **SigLIP 方向相反**：text-only +0.0664 vs both −0.0114（`tools/_siglip_strict_stats.py`，t=−52.7） |
| 5 | **both 在两架构上检索都更强** → 降间隙 ≠ 提检索 |

    python tools\_pa_make_highlights.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_TXT = REPO / "paper合" / "highlights_nc.txt"
OUT_TEX = REPO / "paper合" / "highlights_nc.tex"

TITLE = ("Protect, Don't Perturb: From Empirical Regularities to a Dynamical Theory of Cross-Modal "
         "Alignment under PEFT")

ITEMS = [
    "Adaptation position matters more than adapter configuration",
    "An ODE predicts gap trajectories at median R2 of 0.97",
    "Strict freezing confirms the text-only position on CLIP",
    "The same control reverses the ordering on SigLIP",
    "Lower gap and better retrieval are not the same objective",
]

TEX = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\pagestyle{empty}
\begin{document}
\begin{center}
{\large\bfseries Highlights}
\end{center}
\vspace{0.6em}
\noindent\textbf{%TITLE%}\\[2pt]
Hongrui Wan\\
University of Southampton\\
\emph{Neurocomputing}
\vspace{1.2em}
\begin{itemize}[leftmargin=1.5em,itemsep=0.6em]
%ITEMS%
\end{itemize}
\end{document}
"""


def main() -> int:
    apply = "--apply" in sys.argv
    longest = max(len(x) for x in ITEMS)
    ok = 3 <= len(ITEMS) <= 5 and longest <= 85
    print(f"  条数 {len(ITEMS)}（要求 3–5）｜ 最长 {longest} 字符（要求 ≤85）→ {'✅' if ok else '❌'}")
    for i, x in enumerate(ITEMS, 1):
        print(f"    {i}) {len(x):3d}  {x}")
    if not ok:
        return 1
    txt = "Highlights\n\n" + "\n".join("- " + x for x in ITEMS) + "\n"
    tex = TEX.replace("%TITLE%", TITLE).replace(
        "%ITEMS%", "\n".join("  \\item " + x for x in ITEMS))
    if apply:
        OUT_TXT.write_text(txt, encoding="utf-8")
        OUT_TEX.write_text(tex, encoding="utf-8")
        print(f"  ✅ 写出 {OUT_TXT.name} 与 {OUT_TEX.name}")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
