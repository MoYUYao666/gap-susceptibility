# -*- coding: utf-8 -*-
r"""加入严格冻结的三臂表，并把被否定的小节标题改掉（2026-10-03）。

## 修正我自己上一轮的两处问题

1. 我把设计模式段指向了 `tab:position`，**但那张表是 legacy 约定下的数据**（表注已说明"does not
   isolate a siting choice"）。严格冻结的三臂数据**没有表**，引用是错的 → 新建
   **`tab:position_strict`** 并把引用改过去。
2. 小节标题 `Core Finding: Text-Only Preserves Alignment` 是**一般性声称**，而三骨干三臂结果显示
   在 SigLIP 上相反 → 标题加约定限定，正文首句同样限定。

## 数据（`tools/_pa_three_arm_stats.py`，5 seeds，严格冻结）

| 骨干 | text_only | both | vision_only |
|---|---|---|---|
| CLIP B/32 (WIT) | −0.0465 / 0.624 | −0.0258 / 0.693 | +0.0106 / 0.680 |
| OpenCLIP B/32 (LAION) | +0.0694 / 0.643 | +0.0881 / 0.680 | +0.0925 / 0.672 |
| SigLIP B/16 | +0.0664 / 0.432 | −0.0114 / 0.619 | +0.0522 / 0.341 |

    python tools\_pa_add_strict_table.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

TABLE = r"""
\begin{table}[ht]
\centering
\caption{The three adaptation positions under strict freezing, where the optimiser sees only the adapter
matrices and the arms therefore differ solely in where those adapters sit. Each entry is $\Delta$CG with
$R@1$ beneath it, over five seeds at 5000 samples and 10 epochs with rank $8$ and $\alpha=16$; negative
$\Delta$CG means the gap narrowed. The arms are ordered by $\Delta$CG identically on both B/32 backbones
and identically on neither compared with B/16, and on the two B/32 backbones that ordering is the reverse
of the ordering by $R@1$.}
\label{tab:position_strict}
\begin{tabular}{lccc}
\toprule
Backbone (pre-training) & Text-only & Both & Vision-only \\
\midrule
CLIP ViT-B/32 (WIT)        & $\mathbf{-0.0465}$ \; / \; $0.624$ & $-0.0258$ \; / \; $\mathbf{0.693}$ & $+0.0106$ \; / \; $0.680$ \\
OpenCLIP ViT-B/32 (LAION)  & $\mathbf{+0.0694}$ \; / \; $0.643$ & $+0.0881$ \; / \; $\mathbf{0.680}$ & $+0.0925$ \; / \; $0.672$ \\
SigLIP ViT-B/16            & $+0.0664$ \; / \; $0.432$ & $\mathbf{-0.0114}$ \; / \; $\mathbf{0.619}$ & $+0.0522$ \; / \; $0.341$ \\
\bottomrule
\end{tabular}
\end{table}
"""

OLD_H = r"\subsection{Core Finding: Text-Only Preserves Alignment}"
NEW_H = r"\subsection{The Position Effect Under the Earlier Convention}"

OLD_SENT = (r"The central empirical regularity is shown in Figure~\ref{fig:overview}: \textbf{text-only "
            r"fine-tuning overwhelmingly preserves cross-modal alignment}.")
NEW_SENT = (r"Under the convention used for the runs in this subsection, in which the backbone remains "
            r"trainable alongside the adapter, the central regularity is shown in "
            r"Figure~\ref{fig:overview}: \textbf{text-only fine-tuning overwhelmingly preserves "
            r"cross-modal alignment}. Section~\ref{sec:validation} shows that this conclusion does not "
            r"survive strict freezing on every backbone, and Table~\ref{tab:position_strict} reports the "
            r"strict-freezing comparison.")

OLD_REF = r"as Table~\ref{tab:position} records."
NEW_REF = r"as Table~\ref{tab:position_strict} records."


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_H, NEW_H, "小节标题加约定限定"),
                          (OLD_SENT, NEW_SENT, "首句加限定 + 指向严格表"),
                          (OLD_REF, NEW_REF, "修正表引用为严格表")):
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ {why}：未唯一命中（{c} 次）")
    # 表插到 tab:position 表之后
    anchor = "\\end{table}"
    i = t.find("\\label{tab:position}")
    j = t.find(anchor, i)
    if j < 0:
        print("  ⚠ 未找到 tab:position 表尾")
        return 1
    if "tab:position_strict" not in t:
        print("  ✅ 新表插入点已定位")
        if apply:
            t = t[:j + len(anchor)] + "\n" + TABLE + t[j + len(anchor):]
        n += 1
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "\\label{tab:position_strict}" in t2, "断言失败：新表未写入"
        assert "Core Finding: Text-Only Preserves Alignment" not in t2, "断言失败：旧标题仍在"
        assert "Table~\\ref{tab:position_strict} records" in t2, "断言失败：表引用未改"
        assert "+0.0925" in t2 and "0.341" in t2, "断言失败：三臂数据未写入"
        print(f"\n  ✅ 已改 {n} 处并断言通过")
    else:
        print(f"\n  {n} 处可改（预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
