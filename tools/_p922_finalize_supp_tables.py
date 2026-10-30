# -*- coding: utf-8 -*-
r"""Refresh the staged P3 replacement files and record the supplement table fix.

    python tools/_p922_finalize_supp_tables.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
REV = REPO / "SUBMISSION" / "P3_PRL_revision"
UPLOAD = REV / "UPLOAD_2026-10-15"
CORR = REV / "CORRECTED_2026-10-15"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "P3 补充材料表格已修"

ENT = """> **📐 2026-10-15 14:45 —— P3 补充材料 Table S3 文字被压：已修（5 张表全部改为定宽+按栏缩放）**
>
> 操作者反馈：**「TABLE S3 文字有被压到」**。
>
> ### 一、🔍 根因（读源码 + 量渲染）
>
> `tab:comparison` 用 **`\\begin{tabular}{lcccc}`** 装在 **`table*`** 里 ⇒ **每列都按"自然宽度"**：
>
> * 两个文字列被压到"最长单词"宽度（`IGU-LoRA`、`GFAP (Ours)` 折成两行）；
> * 三个 Yes/No 列反而很宽；
> * **caption 按表格宽度排**，于是**比上面的表线还宽**（截图里 caption 左右都超出表线）；
> * 单元格被 justify 拉伸（该表未设 ragged-right）。
> * 另外 `hyperref` 未设 `hidelinks` ⇒ **每个引用画彩色框**（引文绿框、交叉引用青/红框），
>   这正是"看起来拥挤"的另一半原因。
>
> ### 二、✅ 修法（`tools/_p916` → `_p917` → `_p918` → `_p919`）
>
> | 项 | 处理 |
> |---|---|
> | 列宽 | 全部改为**定宽 `p{}`** + **`\\raggedright`**（短单元格不再被拉伸）|
> | 表宽上限 | 四张单栏表包进 **`\\resizebox{\\columnwidth}{!}{…}`** ⇒ **结构上不可能超出栏宽**；`table*` 那张按文本宽 18.2 cm 手工配宽（12.7 cm）|
> | 字号 | **五张表统一 8 pt / 9.5 pt 行距**（原 `\\footnotesize` 混用）|
> | 表头 | `Rank Allocation Basis`→`Rank basis`、`Phase Transition?`→`Phase?`、`Cross-Arch?`→`Cross-arch?`；`std`→`Std`、`regime`→`Regime`，并加粗 |
> | caption | Table S3 缩到**一行**；Table S5 缩为三行（内容不变）|
> | 链接框 | 补充材料也加 **`\\hypersetup{hidelinks}`**（与正文一致）|
>
> ### 三、⚠️ 过程中踩到的坑（都已修，写进脚本注释）
>
> | # | 坑 | 后果 |
> |---|---|---|
> | ① | 第一版定宽后 **Table S4 比单栏宽 1.19×** | 末列**压进右栏并与正文重叠**；用 `\\resizebox` + 收窄列宽解决 |
> | ② | `\\resizebox{…}{!}{%` 的分组大括号多写一个 | 编译 **101 个 `Missing \\cr inserted`**、无 PDF；脚本加"多余大括号"断言 |
> | ③ | 脚本**不幂等**：二次运行只找 `\\end{tabular}`，匹配不到已闭合的 `\\end{tabular}}` | 误改；已加幂等前置判断 |
> | ④ | 测"栏间空白"时**猜错栏距**（630–690 其实是右栏起点） | 误报每页都有溢出；改为**先测空白带**（实测 626–648 px）再判定 |
>
> ### 四、✅ 复核（`tools/_p920_supp_overflow_check.py`）
>
> | 项 | 结果 |
> |---|---|
> | 编译 | **0 错误 / 0 未定义引用 / 0 未定义引文 / 0 `??`** |
> | **Overfull 盒子** | **hbox 0、vbox 0** |
> | 栏间空白（626–648 px，6 页逐页测）| **全部 clean**（标题与全宽表跨越栏距属正常，已排除标题带）|
> | Table S3 | 方法名**不再折行**，caption **单行**、与表线等宽 |
> | Table S4 | 在栏内，无重叠 |
> | 页数 | 5 → **6 页**（表格变松，参考文献落到第 6 页；补充材料页数无限制）|
> | 逐条对应 | `tools/_p893` → **CORRESPONDENCE VERIFIED**；`tools/_p910` → **NUMBERING CONSISTENT** |
>
> ### 五、交付件
>
> `SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/` 四个 PDF **已用最终版刷新**。
> 工具：`_p915`（看表结构）｜`_p916`（表体重排）｜`_p917`（列表现状）｜`_p918`（按栏缩放）｜
> `_p919`（加宽 Table S3）｜`_p920`（溢出检查）｜`_p921`（栏距定位）｜`_p922`（本条落账）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not a.apply:
        print("  (dry run)")
        return 0

    main_pdf = P3 / "main.pdf"
    supp_pdf = P3 / "supplementary" / "supplementary.pdf"
    for src, dsts in ((main_pdf, ["main.pdf", "P3_PRLETTERS-D-26-02378_Manuscript.pdf"]),
                      (supp_pdf, ["supplementary.pdf", "P3_PRLETTERS-D-26-02378_Supplementary.pdf"])):
        for d in dsts:
            shutil.copy2(src, UPLOAD / d)
    shutil.copy2(main_pdf, CORR / "main_corrected.pdf")
    shutil.copy2(supp_pdf, CORR / "supplementary_corrected.pdf")
    h = {n: hashlib.sha256((UPLOAD / n).read_bytes()).hexdigest() for n in
         ("main.pdf", "P3_PRLETTERS-D-26-02378_Manuscript.pdf",
          "supplementary.pdf", "P3_PRLETTERS-D-26-02378_Supplementary.pdf")}
    assert h["main.pdf"] == h["P3_PRLETTERS-D-26-02378_Manuscript.pdf"]
    assert h["supplementary.pdf"] == h["P3_PRLETTERS-D-26-02378_Supplementary.pdf"]
    print("  replacement files refreshed and byte-identical across the two namings")

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("24. 📐 **P3 补充材料表格已修（2026-10-15 14:45）** —— Table S3 文字被压的根因是 "
           "`tabular{lcccc}` 在 `table*` 里按自然宽排布（文字列被压、caption 比表线宽）+ `hyperref` 未设 "
           "`hidelinks`（满页彩色引用框）。五张表统一 **8 pt + 定宽 `p{}` + `\\raggedright`**，"
           "四张单栏表包 `\\resizebox{\\columnwidth}`（**结构上不会超栏**），表头缩短加粗、caption 缩短。"
           "复核：**Overfull hbox/vbox = 0**，栏间空白 6 页逐页 **clean**，0 错误 0 未定义引用；补充材料 5→**6 页**。"
           "交付件已刷新。详见 `HANDOFF.md` 顶部 2026-10-15 14:45 条目。\n")
    anchor = "23. 🔢 **P3 编号体系已改对（2026-10-15 14:30）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    else:
        print("  WARN: map item 23 not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
