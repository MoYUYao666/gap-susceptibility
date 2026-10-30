# -*- coding: utf-8 -*-
r"""记录 2026-10-06 阶段：patch 尺寸分组写入正文 + BioCLIP 计入计数 + 全量审核。

    python tools\_docs_20261006.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **📐 2026-10-06 —— patch 尺寸分组写入正文；BioCLIP 计入计数；全量审核通过**
>
> 操作者："**写上，同时再次审核**"。
>
> ### ① 写入正文：位置效应按 patch 尺寸分组
>
> 设计模式① 由"B/32 相同、B/16 不同"升级为：
>
> > "across all **seven strict-freezing configurations** measured, every patch-32 backbone has the
> > text-only arm at the smallest gap change and every patch-16 backbone has the both-position arm there,
> > **without exception**."
>
> **并如实写入三条边界**：
>
> | 边界 | 正文表述 |
> |---|---|
> | BioCLIP 仅 rank 4 | "measured at rank~$4$ only" |
> | **BioCLIP 是域外模型** | 初始 CG **1.79** vs B/32 的 **0.81** → "domain shift alone could account for its ordering" |
> | patch 尺寸与骨干未解耦 | "with two backbones per patch size the two are not separated" |
> | **故不作因果表述** | "we report the grouping as a **regularity over seven configurations** rather than as a **property of patch size**" |
>
> 脚本：`tools/_pa_add_patch_grouping.py`、`tools/_pa_add_bioclip_row.py`
>
> ### ② `tab:position_strict` 补齐（**否则正文超表所载**）
>
> 表原只有 3 行，正文却引用"7 个配置"→ **必须补 BioCLIP 行**。改动：
>
> - 加 **Patch 列**（使"按 patch 尺寸分组"读表即可见）；
> - 加 **BioCLIP ViT-B/16 (bio.)** 行，$\Delta$CG 为 −0.3671 / **−0.4515** / −0.2927；
> - **R@1 列写 `---`**——`_exp3_bioclip_strict.py` **没有记录 R@1**，**故留空而非估计**
>   （表注写明"retrievals were not recorded … left blank rather than estimated"）；
> - 表注补 patch 列说明与 BioCLIP 边界。
>
> ### ③ 计数更新：BioCLIP 的 9 个 run 计入
>
> 正文引用 BioCLIP 结果，**实验计数却把它排除**——与"计数应涵盖所报告的实验"不一致（上轮刚修过同类问题）。
>
> | 组 | 原 | 现 |
> |---|---|---|
> | 附录目录（13 类机理 117 + XIV 类严格冻结） | 212 | **221**（严格冻结 95 → **104**） |
> | ODE 拟合 | 162 | 162 |
> | **全文合计** | **374** | **383** |
>
> 目录表 XIV 类由 "three backbones" 改为 "**four backbones**"。
>
> ### ④ 顺带修掉一处硬编码（**同一类问题的又一处**）
>
> `tools/_check_catalog_sum.py` 的"三段口径"一行**硬编码了 95/162/374**——计数一变就会报过期数字。
> 已改为**全部动态读取**（严格冻结 run 从 `outputs/` 实测统计、ODE 与合计从稿件抽取），
> 并新增两条一致性断言。实测输出：
>
> ```
> 实测严格冻结 run : 104（各骨干 95 + BioCLIP 9）
> 论文声明 ODE 拟合 : 162
> 附录目录求和      : 221
> 摘要声明全文合计  : 383
> 目录 + ODE = 221 + 162 = 383  → ✅ 一致
> ✅ 严格冻结实测 104 = 目录表隐含值（221 − 117）
> ```
>
> 脚本：`tools/_fix_catalog_check_dynamic.py`
>
> ### ⑤ 全量审核结果
>
> | 项 | 结果 |
> |---|---|
> | 编译（两版） | NC **45 页** / Springer **33 页**，**0 错误、0 未定义引用** |
> | 引用 | cites **44** = bib **44**，缺失 0、未使用 0 |
> | 结构 | 悬空 `\ref` **0**、重复 label **0**、占位符 **0**、图文件缺 **0** |
> | 编号 | 图 **12/12**、表 **9/9** label 一致 |
> | 摘要 | **244 词** ≤250；两版一致 |
> | 声明 | 5 节齐备且位于文献前 ｜ Highlights 5 条 |
> | 核心主张复算 | 严格冻结 5-seed 方向+排序 ✅；`R²>0.96` ✅ |
> | 三骨干 rank 配对检验 | 5/6 同向显著；位置排序 8/10 |
> | **四骨干 patch 分组** | **patch32 → text_only（4 配置）｜ patch16 → both（3 配置）✅** |
> | 计数 | 目录求和 = Total = **221**；全文 **383**；旧计数残留 **0** |
> | 图来源 | **12/12** 有脚本 + 源 JSON |
> | 投稿包 | 已重建（**45 页**），终检全绿 |
>
> ### ⑥ 审核中发现并修正的**流程问题**
>
> | 现象 | 真相 |
> |---|---|
> | `pdfinfo main_nc.pdf` = **45 页**，而终检脚本报 **43 页** | 终检脚本读的是 `NC_submission/Manuscript.pdf`（**过期副本**）→ **必须重建投稿包后再看终检**，否则读数滞后 |
> | 页数 43 → 45 | 新表列 + 表注 + 新段所致；已同步 5 个文档的页数记录（9 处） |
>
> ### ⑦ 结论
>
> **Paper A 可投**：NC **45 页**、Springer **33 页**、引用 44 条全匹配、图 12 张来源明确、
> 4 个骨干的严格冻结对照、理论根基与机制均经**直接**验证。
> **唯一未决变量仍是 P1（`PR-D-26-10149`）的决定。**

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "patch 尺寸分组写入正文" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **🧬 2026-10-06 —— BioCLIP 部分结果"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("patch 尺寸分组写入正文", "221", "383", "left blank rather than estimated", "45 页"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
