# -*- coding: utf-8 -*-
r"""按**预训练目标**改写 patch-size 规律（操作者选①）——**按 label 定位，按行号替换**。

## 上一版失败原因（两次）

| 版 | 失败 | 教训 |
|---|---|---|
| 1 | 手打 caption 字符串跨行 → **命中 0** | 长字符串跨行匹配易错 |
| 2 | 找**第一个** `\caption{` → 改到了 `fig:overview`（**图的 caption**），且断言抓出旧措辞仍在 | **必须按 label 定位，不能按"第一个 caption"** |

**本版**：先找 `\label{tab:position_strict}`，再**向上**找该表自己的 `\caption{` 起止，
**按行号替换**；表体行也按行号替换。

## 改什么

| 处 | 原文 | 改为 |
|---|---|---|
| 表 caption | "The patch column is what the ordering tracks: every patch-32 … every patch-16 …" | "**Rows are grouped by pre-training objective**, which is what the ordering tracks…" |
| 表体 | 5 行 | **6 行 + 分组小标题**（新增 `CLIP B/32†`、`CLIP B/16†`，均 @ r4 同秩） |
| 规律句 | "every patch-32 backbone … every patch-16 …, without exception" | 按**预训练目标**分组 + **同秩对照** |

    python tools\_pa_group_by_pretraining3.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

CAP_OLD_MARK = "The patch column is what the ordering tracks"
CAP_NEW = [
    r"\caption{The three adaptation positions under strict freezing, where the optimiser sees only the adapter",
    r"matrices and the arms therefore differ solely in where those adapters sit. Each entry is $\Delta$CG with",
    r"$R@1$ beneath it (bold marks the smallest $\Delta$CG in the row), at 5000 samples and 10 epochs with",
    r"$\alpha=2r$; negative $\Delta$CG means the gap narrowed. Rows are grouped by pre-training objective, which",
    r"is what the ordering tracks: every contrastive image--text backbone puts text-only smallest, and the two",
    r"backbones trained with other objectives put both there. Patch size does not separate the groups, and the",
    r"two rows marked $\dagger$ show this directly, having been measured at the same rank under the same",
    r"protocol: CLIP B/16 and CLIP B/32 order the arms identically despite differing in patch size by a factor",
    r"of two. On the contrastive backbones the arm that minimises the gap (text-only) retrieves worst, so the",
    r"ordering by gap runs opposite to the ordering by $R@1$; SigLIP orders them differently on both counts.",
    r"BioCLIP was measured at rank~$4$ over three seeds and its retrievals were not recorded, so those cells are",
    r"left blank rather than estimated; its pre-training corpus is biological, so its absolute $\Delta$CG is not",
    r"comparable with the others and only its within-row ordering is used. The $\dagger$ rows are single-seed",
    r"runs under the same protocol, whereas the archived rows are five-seed means; on CLIP B/32 the seed-to-seed",
    r"standard deviation is $0.003$, so the gaps those single runs separate are several times that spread. On",
    r"OpenCLIP the gap between adjacent arms is the smallest of any backbone here, at about twice the archived",
    r"seed-to-seed deviation, and its ordering should be read with that in mind.}",
]

ROWS_OLD_FIRST = r"CLIP B/32 (WIT)      & 32 & $\mathbf{-0.0465}$ / $0.624$"
ROWS_NEW = [
    r"\multicolumn{5}{@{}l}{\textit{Contrastive image--text pre-training}}\\",
    r"CLIP B/32 (WIT)      & 32 & $\mathbf{-0.0465}$ / $0.624$ & $-0.0258$ / $\mathbf{0.693}$ & $+0.0106$ / $0.680$ \\",
    r"OpenCLIP B/32 (LAION)& 32 & $\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$ \\",
    r"CLIP B/32$^\dagger$ (WIT) & 32 & $\mathbf{-0.0297}$ / $0.625$ & $-0.0186$ / $\mathbf{0.680}$ & $+0.0124$ / $0.668$ \\",
    r"CLIP B/16$^\dagger$ (WIT) & 16 & $\mathbf{-0.0190}$ / $0.642$ & $+0.0150$ / $\mathbf{0.696}$ & $+0.0433$ / $0.677$ \\",
    r"\midrule",
    r"\multicolumn{5}{@{}l}{\textit{Other objectives}}\\",
    r"SigLIP B/16 (WebLI)  & 16 & $+0.0664$ / $0.432$ & $\mathbf{-0.0114}$ / $\mathbf{0.619}$ & $+0.0522$ / $0.341$ \\",
    r"BioCLIP B/16 (bio.)  & 16 & $-0.3671$ / --- & $\mathbf{-0.4515}$ / --- & $-0.2927$ / --- \\",
]

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
    lines = io.open(F, encoding="utf-8").read().splitlines()
    lab = next((i for i, l in enumerate(lines) if r"\label{tab:position_strict}" in l), None)
    if lab is None:
        print("  ❌ 未找到 label")
        return 1
    cap_s = next((i for i in range(lab, -1, -1) if lines[i].lstrip().startswith(r"\caption{")), None)
    cap_e = next(i for i in range(cap_s, lab + 1) if lines[i].rstrip().endswith("}"))
    print(f"  ✅ 按 label 定位：表 caption L{cap_s+1}–L{cap_e+1}（{cap_e-cap_s+1} 行）")
    if CAP_OLD_MARK not in "\n".join(lines[cap_s:cap_e + 1]):
        print("  ⚠ caption 里没有预期旧标记 → 可能已改")
        return 1
    # 表体：找第一行以 CLIP B/32 (WIT) 开头
    r0 = next((i for i, l in enumerate(lines) if l.startswith("CLIP B/32 (WIT)")), None)
    if r0 is None:
        print("  ❌ 未找到表体首行")
        return 1
    r1 = next(i for i in range(r0, len(lines)) if lines[i].startswith("BioCLIP B/16"))
    print(f"  ✅ 表体 L{r0+1}–L{r1+1}（{r1-r0+1} 行）")
    if not apply:
        print("  （预演）")
        return 0
    new = (lines[:cap_s] + CAP_NEW + lines[cap_e + 1:r0] + ROWS_NEW + lines[r1 + 1:])
    t = "\n".join(new) + "\n"
    if SENT_OLD in t:
        t = t.replace(SENT_OLD, SENT_NEW, 1)
        print("  ✅ 规律句已替换")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("Rows are grouped by pre-training objective", "What separates the two orderings is the",
              r"CLIP B/16$^\dagger$", "Other objectives", "Contrastive image--text pre-training"):
        assert k in t2, f"断言失败：缺 {k}"
    for k in ("The patch column is what the ordering tracks",
              "every patch-16 backbone puts both there",
              "every patch-16 backbone has the both-position arm"):
        assert k not in t2, f"断言失败：旧措辞仍在：{k}"
    # 保护 fig:overview 未被误改
    assert "Modality gap evolution during PEFT" in t2, "断言失败：fig:overview 的 caption 被改坏了"
    print("  ✅ 已写入：表 caption + 6 行表体 + 规律句；并断言 fig:overview 未被误改")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
