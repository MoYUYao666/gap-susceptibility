# -*- coding: utf-8 -*-
r"""Record the page-49 float fix, the palette unification, and the broken fig4 that it uncovered.

Three defects were found by measuring rather than looking, and all three are fixed:

1. **Page 49 overran the footer by ~90 pt.** Rendering every page and taking the lowest ink row gives
   702.2 pt (the footer baseline) on 48 pages and 791.5 pt -- the paper edge -- on page 49. Profiling
   the page shows the cause: the caption of Table 2 plus a provenance note under the table was about a
   page and a half of prose above a six-row table. The caption now carries only what is needed to read
   the table, and the provenance became Section F of the appendix. Re-measured after the fix: the
   maximum last-ink row across all 62 pages is 702.2 pt, i.e. no page overruns and the page number
   stays in the footer.
2. **fig4.pdf was the wrong figure.** The manuscript includes `fig4.pdf`, but the cross-method
   comparison had only ever been written as a PNG (`_pa_rebuild_fig4_crossmethod.py` saves PNG only),
   so the PDF still held the old beta-vs-dimension plot whose legend labels were `False` and `True`.
   Worse, `_pa_rebuild_figs_rest.py::fig_crossmethod` rewrote the *PNG* with the same wrong plot, so
   running the rebuild chain silently reverted the fix. That function is now disabled, and fig4 is
   regenerated from the correct sources.
3. **Three figures drew data outside the shared palette** (fig1 and fig2 in matplotlib's default blue,
   orange and green; fig4 carried the same defaults; fig15 used crimson). All four now use Okabe-Ito,
   and `tools/_p871_figure_palette.py` measures this from the drawings so it cannot drift again.

    python tools/_p873_record_figure_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "页 49 溢出与图库配色已全修"

ENT = """> **📐 2026-10-15 13:40 —— 页 49 溢出与图库配色已全修（并查出 fig4 是「错的图」）**
>
> 操作者指令：**「49页最下面什么情况，所有16张图片你注意配色统一，全部修好」**。
>
> ### 一、✅ 页 49 到底是什么问题 —— **正文压到纸边，页码被挤出页脚**
>
> **实测**（`pdftoppm -r 150` 逐页渲染，取每页最低墨迹行）：
>
> | 项 | 实测 |
> |---|---|
> | 48 页的最低墨迹行 | **702.2 pt = 页脚基线**（正常）|
> | **第 49 页** | **791.5 pt = 纸面下边（792 pt）** ⇒ **越出页脚约 90 pt**，页码被挤到纸最底 |
> | 全稿其它页 | 无一越界 |
>
> **根因**：第 49 页**整页都是 Table 2 的图注**（逐行剖面证实：全页为通栏文字，表格在最末几行）。
> 图注 + 表下出处注 ≈ **一页半**，压在 6 行表上 —— **任何这么大的图注都不可能不越界**。
>
> **修法**（按用途拆分，**未删任何内容**）：
>
> | 内容 | 去处 |
> |---|---|
> | 读表必需（协议、seed、分组、† 行、gap 与 R@1 排序相反）| **留在图注**（19 行 → 14 行）|
> | R@1 列的出处（OpenCLIP rank-8/rank-4 两半错配、CLIP B/32 text-only 用了非严格均值、vision-only 那格无法复现）| **移入附录新增 F 节**（`\\label{sec:r1provenance}`），图注指向它 |
> | 图注内**重复的同一句**（"Every row is a five-seed mean …" 出现两次）| 合并为一句 |
>
> **修后实测**：**62 页全部最低墨迹行 = 702.2 pt**（页脚基线），**无任何页越界**；`Float too large for page` 警告 **1 → 0**。
>
> ### 二、✅ 配色统一：**17/17 张图只用 Okabe-Ito 调色板**（`tools/_p871_figure_palette.py` 从图形本身测）
>
> | 图 | 原有外来色 | 改为 |
> |---|---|---|
> | `fig1` | **`#1f77b4` / `#ff7f0e` / `#2ca02c`**（matplotlib 默认三色）| 灰 `#666666` 点线 / 蓝 `#0072B2` 实线 / 朱红 `#D55E00` 虚线（**线型冗余编码**）|
> | `fig2` | **`#1f77b4` / `#ff7f0e`** | 蓝 `#0072B2`（DG）/ 朱红 `#D55E00`（CG）|
> | `fig4` | 同默认色（且是**错的图**，见下）| 蓝（LoRA）/ 朱红（Adapter，斜纹冗余）|
> | `fig15` | **`#d62728`** 猩红 | 蓝（flickr30k）/ 绿 `#009E73`（coco）；柱状图蓝/朱红 |
>
> **判据**：脚本把每张图 PDF 渲染成位图，剔除灰/黑/白后，把每个彩色像素与调色板**及调色板两两之间的混色线段**比较（覆盖抗锯齿与 alpha 混合），并忽略 <120 px 的碎色（字形羽化）。**残留外来色：0。**
>
> ### 三、⚠️ 顺带查出：**`fig4.pdf` 是「错的图」，而且已经错了几个月**
>
> | 项 | 实况 |
> |---|---|
> | 稿件引用的 | **`figures/fig4.pdf`** |
> | 2026-10-06 的"重做" | `_pa_rebuild_fig4_crossmethod.py` **只写了 PNG**、**从未写 PDF** |
> | 后果 | **LaTeX 里一直是旧图**：`β` vs Adapter 维度，图例标签是 **`False` / `True`** |
> | **更糟** | `_pa_rebuild_figs_rest.py::fig_crossmethod` 会把**同一个错图写回 `fig4.png`** ⇒ **重跑重绘链会把修好的图again覆盖**（我本次就中了一次）|
>
> **修法**：① 停用 `fig_crossmethod`（保留函数与 docstring 作为记录）；② 用正确数据重出 `fig4.pdf` + `.png`（LoRA 三臂 −0.047/−0.026/+0.011 vs Adapter +0.185/+0.229，即图注声称的模式）。
> **该脚本的 PNG-only 写法也在 `fig2_v5_falsification`、`fig4_effective_rank` 上出现过**（其 PDF 停在 2026-08-02）—— 一并改为共享 `save()`。
>
> ### 四、✅ 四件查图工具（幂等，可重跑）
>
> | 脚本 | 作用 |
> |---|---|
> | `tools/_p871_figure_palette.py` | **从图形**测配色（含混色判定）——外来色即 FAIL |
> | `tools/_p867_figure_audit.py` | 引用/孤儿/PDF-PNG 成对/字体四项 |
> | `tools/_p868_figure_scale.py` | 自然宽 vs 要求宽（缩放倍率）|
> | `tools/_p872_fix_table_float.py` | 表 2 图注压缩 + 出处移入附录 F |
>
> ### 五、✅ 复核
>
> | 项 | 结果 |
> |---|---|
> | 编译 | **62 页 / 0 错误 / 0 未定义引用 / 0 `Float too large`** |
> | 页面越界 | **0/62**（全部止于 702.2 pt）|
> | 配色 | **17/17** 仅 Okabe-Ito |
> | 字体 | **17/17** Times New Roman + STIX |
> | 缩放 | **17/17** 1.00× |
> | 台账 | `_claim_ledger_paperA.py` **PASS 52 ｜ GAP 0**；`_claim_ledger.py` **80/80** |
> | `NC_submission` 副本 | 图 34/34 SHA-256 一致；tex 同步 |
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK in hp:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0

    i = hp.find("# 项目交接文档")
    j = hp.find("\n", i)
    hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("16. 📐 **页 49 溢出 + 配色统一已修（2026-10-15）** —— 实测页 49 正文压到纸边（791.5 pt，"
           "越出页脚 ~90 pt）⇒ **图注压缩 + R@1 出处移入附录 F 节**；修后 **62 页全部止于 702.2 pt，0 越界**。"
           "配色 **17/17 只用 Okabe-Ito**（fig1/fig2/fig4 原为 matplotlib 默认色，fig15 原为猩红）。"
           "⚠️ 顺带查出 **`fig4.pdf` 一直是错的图**（`β` vs dim，图例 `False`/`True`）——重做脚本只写 PNG，"
           "且 `_pa_rebuild_figs_rest.py::fig_crossmethod` 会把错图写回，**已停用**。"
           "查图四件套：`_p871_figure_palette.py`、`_p867_figure_audit.py`、`_p868_figure_scale.py`、"
           "`_p872_fix_table_float.py`。详见 `HANDOFF.md` 顶部 2026-10-15 13:40 条目。\n")
    anchor = "15. 🖼️ **图库复核（2026-10-15）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
    else:
        print("  WARN: map item 15 not found; map not updated")

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("791.5 pt", "702.2 pt", "17/17", "False", "fig_crossmethod", "62 页"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
