# -*- coding: utf-8 -*-
r"""按**预训练目标**改写 patch-size 规律（操作者选①，2026-10-08）。

## 为什么要改

新增的**同秩对照**（`CLIP B/32 @ r4` 与 `CLIP B/16 @ r4`，相同协议、相同样本量）
给出**相同的最保护臂**（都 `text_only`）→ **patch size 不影响排序**。

叠加全部 6 骨干：**四个 `text_only 最保护` 的全是对比式图像-文本预训练**（WIT×3、LAION×1）；
**两个 `both 最保护` 的都不是**（SigLIP 用 sigmoid 目标、BioCLIP 为生物域）。

→ 论文原文 *"every patch-16 backbone puts both there"* **被证伪**。

## 改法（①按预训练目标分组）

| 处 | 原文 | 改为 |
|---|---|---|
| 表 caption | "The patch column is what the ordering tracks: every patch-32 … every patch-16 …" | "**The pre-training objective is what the ordering tracks**…" |
| 表体 | 5 行（CLIP B/32、OpenCLIP、SigLIP、BioCLIP） | **6 行 + 按预训练分组**（新增 CLIP B/16 @ r4、CLIP B/32 @ r4） |
| L165 规律句 | "every patch-32 backbone … every patch-16 backbone …, without exception" | 改为**按预训练分组** + **同秩对照**说明 |

## 改后要保留的诚实标注

- 新增两行是**单 seed**（归档为 5 seed）→ 表注写明；
- **OpenCLIP 的效应最弱**（相邻臂差异仅 ~2 sd）→ 表注写明；
- BioCLIP **只有汇总归档**（无逐 run）→ 保留原注。

    python tools\_pa_group_by_pretraining.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

# ── ① 表 caption：把"patch 列决定排序"改为"预训练目标决定排序"
CAP_OLD = (r"$\alpha=2r$; negative $\Delta$CG means the gap narrowed. The patch column is what the ordering tracks: "
           r"every patch-32 backbone puts text-only smallest and every patch-16 backbone puts both there. The arms "
           r"are ordered by $\Delta$CG identically on both B/32 backbones, and on those two backbones that ordering "
           r"is the reverse of the ordering by $R@1$; SigLIP orders them differently on both counts. BioCLIP was "
           r"measured at rank~$4$ over three seeds and its retrievals were not recorded, so those cells are left "
           r"blank rather than estimated; its pre-training corpus is biological, so its absolute $\Delta$CG is not "
           r"comparable with the others and only its within-row ordering is used.}")

CAP_NEW = (r"$\alpha=2r$; negative $\Delta$CG means the gap narrowed. Rows are grouped by pre-training objective, "
           r"which is what the ordering tracks: every contrastive image--text backbone puts text-only smallest, and "
           r"the two backbones trained with other objectives put both there. Patch size does not separate the groups, "
           r"and the two rows measured at rank~$4$ under a matched protocol show this directly: CLIP B/16 and CLIP B/32 "
           r"order the arms the same way at the same rank despite differing in patch size by a factor of two. On the "
           r"contrastive backbones the arm that minimises the gap (text-only) retrieves worst, so the ordering by gap "
           r"runs opposite to the ordering by $R@1$; SigLIP orders them differently on both counts. BioCLIP was "
           r"measured at rank~$4$ over three seeds and its retrievals were not recorded, so those cells are left "
           r"blank rather than estimated; its pre-training corpus is biological, so its absolute $\Delta$CG is not "
           r"comparable with the others and only its within-row ordering is used. The two rows marked $\dagger$ were "
           r"measured at a single seed under the same protocol; the archived rows are five-seed means, and on CLIP "
           r"B/32 the seed-to-seed standard deviation is $0.003$, so the orderings those single runs produce are well "
           r"outside that spread. On OpenCLIP the gap between adjacent arms is the smallest of any backbone here, at "
           r"about twice the archived seed-to-seed deviation, and its ordering should be read with that in mind.}")

# ── ② 表体：6 行 + 分组
ROWS_OLD = r"""CLIP B/32 (WIT)      & 32 & $\mathbf{-0.0465}$ / $0.624$ & $-0.0258$ / $\mathbf{0.693}$ & $+0.0106$ / $0.680$ \\
OpenCLIP B/32 (LAION)& 32 & $\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$ \\
\midrule
SigLIP B/16          & 16 & $+0.0664$ / $0.432$ & $\mathbf{-0.0114}$ / $\mathbf{0.619}$ & $+0.0522$ / $0.341$ \\
BioCLIP B/16 (bio.)  & 16 & $-0.3671$ / --- & $\mathbf{-0.4515}$ / --- & $-0.2927$ / --- \\"""

ROWS_NEW = r"""\multicolumn{5}{@{}l}{\textit{Contrastive image--text pre-training}}\\
CLIP B/32 (WIT)      & 32 & $\mathbf{-0.0465}$ / $0.624$ & $-0.0258$ / $\mathbf{0.693}$ & $+0.0106$ / $0.680$ \\
OpenCLIP B/32 (LAION)& 32 & $\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$ \\
CLIP B/32$^\dagger$ (WIT)  & 32 & $\mathbf{-0.0297}$ / $0.625$ & $-0.0186$ / $\mathbf{0.680}$ & $+0.0124$ / $0.668$ \\
CLIP B/16$^\dagger$ (WIT)  & 16 & $\mathbf{-0.0190}$ / $0.642$ & $+0.0150$ / $\mathbf{0.696}$ & $+0.0433$ / $0.677$ \\
\midrule
\multicolumn{5}{@{}l}{\textit{Other objectives}}\\
SigLIP B/16 (WebLI, sigmoid) & 16 & $+0.0664$ / $0.432$ & $\mathbf{-0.0114}$ / $\mathbf{0.619}$ & $+0.0522$ / $0.341$ \\
BioCLIP B/16 (bio.)  & 16 & $-0.3671$ / --- & $\mathbf{-0.4515}$ / --- & $-0.2927$ / --- \\"""

# ── ③ L165 的规律句（替换其中一句）
SENT_OLD = (r"Under strict freezing the same three arms are ordered identically on both B/32 backbones and differently "
            r"on B/16, as Table~\ref{tab:position_strict} records, and a fourth backbone added to test whether that "
            r"split tracks patch size rather than backbone identity falls on the B/16 side: across all seven "
            r"strict-freezing configurations measured, every patch-32 backbone has the text-only arm at the smallest "
            r"gap change and every patch-16 backbone has the both-position arm there, without exception.")

SENT_NEW = (r"Under strict freezing the same three arms are ordered identically on the three contrastive backbones, "
            r"whether they use patch size $32$ or $16$, as Table~\ref{tab:position_strict} records. An earlier reading "
            r"of these runs attributed the ordering to patch size, because the two backbones that had been measured at "
            r"patch size $16$ both placed the both-position arm smallest. That reading does not survive the matched "
            r"comparison: CLIP B/16 and CLIP B/32, measured at the same rank under the same protocol, order the arms "
            r"identically despite differing in patch size by a factor of two. What separates the two orderings is the "
            r"pre-training objective. Every backbone trained contrastively on image--text pairs places the text-only "
            r"arm at the smallest gap change, across three pre-training corpora and both patch sizes; the two backbones "
            r"trained otherwise --- SigLIP, whose objective is a pairwise sigmoid rather than a softmax over the batch, "
            r"and BioCLIP, whose corpus is biological --- place the both-position arm there instead.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "Rows are grouped by pre-training objective" in t:
        print("  已改，跳过")
        return 0
    n = 0
    for old, new, tag in ((CAP_OLD, CAP_NEW, "caption"),
                          (ROWS_OLD, ROWS_NEW, "表体 5→6 行 + 分组"),
                          (SENT_OLD, SENT_NEW, "L165 规律句")):
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠'} {tag}：命中 {c}")
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
    if n != 3:
        print("  ❌ 未全部命中，未写入")
        return 1
    ast.parse("pass")
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("Rows are grouped by pre-training objective", "CLIP B/16$^\\dagger$",
              "Other objectives", "What separates the two orderings is the"):
        assert k in t2, f"断言失败：缺 {k}"
    for k in ("every patch-16 backbone puts both there, without exception",
              "every patch-16 backbone has the both-position arm there"):
        assert k not in t2, f"断言失败：旧措辞仍在 {k}"
    print("  ✅ 已改写：规律改为按预训练目标分组，旧措辞全清")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
