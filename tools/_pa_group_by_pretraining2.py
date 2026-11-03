# -*- coding: utf-8 -*-
r"""按**预训练目标**改写 patch-size 规律（操作者选①）——按**实际文件内容**匹配 caption。

## 为什么重写

第一版手打了 caption 字符串，**换行位置与实际不符 → 命中 0**。
**教训（本项目已多次）：长字符串跨行匹配很容易错，应先从文件读出来再改。**

## 本版做法

**逐行定位**：找到 caption 的起止行（`\caption{` 到匹配的 `}`），
**按行号替换整段**，不依赖我手打的换行。

    python tools\_pa_group_by_pretraining2.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

CAP_NEW_LINES = [
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
    lines = io.open(F, encoding="utf-8").read().splitlines(keepends=True)
    # 定位 caption 起止：从 \caption{ 到行尾以 } 结束（caption 是独立多行块）
    start = next((i for i, l in enumerate(lines) if l.lstrip().startswith(r"\caption{")), None)
    if start is None:
        print("  ❌ 未找到 caption")
        return 1
    end = next((i for i in range(start, len(lines)) if lines[i].rstrip().endswith("}")), None)
    print(f"  caption 位于 L{start+1}–L{end+1}（原 {end-start+1} 行 → 新 {len(CAP_NEW_LINES)} 行）")
    if end is None:
        return 1
    if "Rows are grouped by pre-training objective" in "".join(lines):
        print("  已改，跳过")
        return 0
    if not apply:
        print("  （预演）")
        return 0
    new = lines[:start] + [l + "\n" for l in CAP_NEW_LINES] + lines[end + 1:]
    t = "".join(new)
    if SENT_OLD in t:
        t = t.replace(SENT_OLD, SENT_NEW, 1)
        print("  ✅ 规律句已替换")
    else:
        print("  ⚠ 规律句未命中（可能上一版已改）")
    ast.parse("pass")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("Rows are grouped by pre-training objective",
              "What separates the two orderings is the",
              "seed-to-seed"):
        assert k in t2, f"断言失败：缺 {k}"
    for k in ("every patch-16 backbone puts both there",
              "every patch-16 backbone has the both-position arm"):
        assert k not in t2, f"断言失败：旧措辞仍在：{k}"
    print("  ✅ 已写入：caption 与规律句均改为按预训练目标分组")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
