# -*- coding: utf-8 -*-
r"""完成严格三臂表的写入与首句限定（修正上一轮的匹配失败）。

## 上一轮为何失败

1. **首句匹配失败**：我按"单词间单空格"写匹配串，但源文件在该处**有换行** → 未命中。
2. **表未插入**：`TABLE` 字符串自带前置换行，而插入逻辑用 `t.find("\\end{table}", i)` 定位后又追加
   `"\n" + TABLE`，且 `if "tab:position_strict" not in t` 的判断在**同一轮内**先于写入执行 →
   表面走通但实际未落盘（断言把它拦住了，这正是断言的价值）。

改法：用**唯一锚点字符串**做插入，并对首句用**正则**跨空白匹配。

    python tools\_pa_add_strict_table2.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

TABLE = r"""\begin{table}[ht]
\centering
\caption{The three adaptation positions under strict freezing, where the optimiser sees only the adapter
matrices and the arms therefore differ solely in where those adapters sit. Each entry is $\Delta$CG with
$R@1$ beneath it, over five seeds at 5000 samples and 10 epochs with rank $8$ and $\alpha=16$; negative
$\Delta$CG means the gap narrowed. The arms are ordered by $\Delta$CG identically on both B/32 backbones,
and on those two backbones that ordering is the reverse of the ordering by $R@1$; SigLIP orders them
differently on both counts.}
\label{tab:position_strict}
\begin{tabular}{lccc}
\toprule
Backbone (pre-training) & Text-only & Both & Vision-only \\
\midrule
CLIP ViT-B/32 (WIT)        & $\mathbf{-0.0465}$ / $0.624$ & $-0.0258$ / $\mathbf{0.693}$ & $+0.0106$ / $0.680$ \\
OpenCLIP ViT-B/32 (LAION)  & $\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$ \\
SigLIP ViT-B/16            & $+0.0664$ / $0.432$ & $\mathbf{-0.0114}$ / $\mathbf{0.619}$ & $+0.0522$ / $0.341$ \\
\bottomrule
\end{tabular}
\end{table}

"""

SENT_PAT = re.compile(
    r"The central empirical regularity is shown in Figure~\\ref\{fig:overview\}: "
    r"\\textbf\{text-only\s+fine-tuning overwhelmingly preserves cross-modal alignment\}\.",
    re.S)
SENT_NEW = (r"Under the convention used for the runs in this subsection, in which the backbone remains "
            r"trainable alongside the adapter, the central regularity is shown in "
            r"Figure~\ref{fig:overview}: \textbf{text-only fine-tuning overwhelmingly preserves "
            r"cross-modal alignment}. Section~\ref{sec:validation} shows that this conclusion does not "
            r"survive strict freezing on every backbone, and Table~\ref{tab:position_strict} reports the "
            r"strict-freezing comparison.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    changed = []

    # ① 插入表：锚在 tab:position 表的 \label{tab:position_strict} 之前不存在的前提下，
    #    用该表之后的下一个 \subsection 作为锚点（唯一且稳定）
    if "\\label{tab:position_strict}" not in t:
        anchor = "\\subsection{LoRA Configuration Space}"
        if anchor not in t:
            print("  ⚠ 未找到插入锚点")
            return 1
        t = t.replace(anchor, TABLE + anchor, 1)
        changed.append("新表 tab:position_strict")

    # ② 首句限定（跨空白匹配）
    m = SENT_PAT.search(t)
    if m:
        t = t[:m.start()] + SENT_NEW + t[m.end():]
        changed.append("首句加约定限定")
    else:
        print("  ⚠ 首句仍未匹配")

    print("  将改：" + "、".join(changed))
    if apply and changed:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "\\label{tab:position_strict}" in t2, "断言失败：新表未写入"
        assert "does not survive strict freezing on every backbone" in t2, "断言失败：首句未限定"
        assert "+0.0925" in t2 and "0.341" in t2, "断言失败：三臂数据未写入"
        assert re.search(r"\\begin\{table\}", t2), "断言失败：表环境丢失"
        # 表编号唯一
        assert t2.count("\\label{tab:position_strict}") == 1, "断言失败：新表重复"
        print("  ✅ 已写入并断言通过")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
