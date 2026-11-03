# -*- coding: utf-8 -*-
r"""Record the P3 paragraph-indentation answer and the three render fixes.

Operator question (2026-10-15): "P3正文每段前是否都已加两个空格，Theorem III.2渲染的得有点奇怪你看看".

Answer to the first part: indentation is present and uniform. Measured from the rendered page, text lines
start at one of two positions -- flush at the margin (columns 102-106 of a 1275-px-wide page) or indented
(column 125, i.e. about 11 pt, the class's `\parindent`) -- so every continuation paragraph is indented
and the only flush lines are a paragraph's first line after a heading or a display.

Second part: three faults found and fixed, all far more visible than the indentation.

    python tools/_p906_record_p3_render.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "P3 段首缩进已核 + 三处渲染缺陷已修"

ENT = """> **🔤 2026-10-15 14:25 —— P3 段首缩进已核（正常）；并修掉三处渲染缺陷（定理头无空格 / 重复 label / 链接绿框）**
>
> 操作者问：**「P3正文每段前是否都已加两个空格，Theorem III.2渲染的得有点奇怪你看看」**。
>
> ### 一、✅ 段首缩进：**有，且全稿一致**（像素实测）
>
> 把第 1、2 页按 150 dpi 渲染后逐行取"最左墨迹列"：
>
> | 行首列 | 出现次数 | 含义 |
> |---|---|---|
> | **102–106 px** | **458** | **顶格行** = 标题下第一段首行、或紧接公式/列表后的首行 |
> | **125 px** | **36** | **缩进行**（比顶格多 **≈23 px ≈ 11 pt**，即 `elsarticle` 的 `\\parindent`）|
>
> **⇒ 每个"续段"都缩进（约两个字符宽），只有"标题下第一段"顶格**——这是 LaTeX/Elsevier 的标准做法
> （IEEE、Elsevier 期刊均如此，**不是漏加**）。正文未设 `\\parindent`，即用类默认值。
> 若操作者希望**标题下第一段也缩进**，需加 `\\usepackage{indentfirst}`——**这会改变已投稿件的观感**，故**未擅自改**。
>
> ### 二、🔴 定理头缺空格（就是"渲染奇怪"的主因）
>
> 截图实测：**`Theorem III.1(Representation Theorem).`**、**`Definition III.1(Gap Susceptibility).`** ——
> 编号与括号说明之间**没有空格**。根因：`IEEEtran` 自带的定理样式把"头后标点"留空。
>
> **修法**（`tools/_p905_p3_render_fixes.py`，**三份主稿变体同时改**，防不一致）：
> 在导言区定义两个 `\\newtheoremstyle`（`p3plain` / `p3defn`）——
> 头后标点 `.`、**头后间距 5pt**、正文**正体**（IEEE 论文的定理陈述惯例，原先被设成斜体）、
> 上下间距各 5pt；并保留 `[section]` / `[theorem]` 计数方式**不变**。
> **标题/编号/正文一字未改**，只改排版参数。
>
> ### 三、🔴 顺手查出并修掉的两处
>
> | # | 缺陷 | 证据 | 修法 |
> |---|---|---|---|
> | ① | **label 重复**：`\\label{lem:r3-not-r3p}` **同时贴在**定义（Gap Susceptibility）与引理（R3 不蕴含 R3′）上 ⇒ `\\ref` 可解析到**任一** | `sections/theory.tex:37` 与 `:44` | 定义改用新 label `def:gap-susceptibility`；引理的 label 保留（正文 2 处 `\\ref` 指向它）|
> | ② | **链接绿框**：`main.tex` 加载 `hyperref` 但**未给 `hypersetup`** ⇒ 每个引用/文献处画**绿色矩形**（投稿 PDF 里满页都是）| 第 2 页实测 **2224 个绿色像素**；`main.log` 无 `colorlinks`/`hidelinks` | 加 `\\hypersetup{hidelinks}`（**保留超链接，只去掉框**）⇒ 实测**绿色像素 0** |
>
> ### 四、✅ 复核（两份重编）
>
> | 项 | 结果 |
> |---|---|
> | `main.pdf` | **10 页 / 0 错误 / 0 未定义引用 / 0 未定义引文** |
> | `supplementary.pdf` | **5 页 / 0 错误 / 0 未定义引用 / 0 未定义引文** |
> | 定理头 | 现为 **`Theorem III.1 (Representation Theorem).`**（有空格）|
> | 绿色链接框 | **0** |
> | 逐条对应 | `tools/_p893_p3_correspondence.py` → **CORRESPONDENCE VERIFIED** |
> | 替换件 | `UPLOAD_2026-10-15/` 四个文件**已用新编版刷新**（`main.pdf` 与稿号名版 SHA-256 相同）|
>
> ### 五、⚠️ 记录在案、**未改**的两项（要改请指示）
>
> | 项 | 现状 | 说明 |
> |---|---|---|
> | **"Corollary 1–5" 其实是 `\\subsection` 标题** | 打印出来是 **`III.D. Corollary 1: First-Order Gradient Flow`**（小节号 + 文字），正文里 `Corollary~4`／`Corollary~5` 是**手写文字**（theory/discussion/experiments/appendix 共 6 处）| 若改成真正的 `corollary` 环境与 `\\ref`，**小节号会消失**（视觉变化），且补充材料里手写的 `Corollary~5` 需同步 |
> | **`Lemma III.1.1`** | 引理按 `[theorem]` 计数 ⇒ 挂在定理 III.1 下 | 自洽，但可读性一般；改为 `[section]` 会变 `III.2`，需同步补充材料里手写的 `Lemma~1` |
>
> **⇒ 这两项都属"编号体系"改动、会牵动补充材料，**没有擅自做**。**
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
    row = ("22. 🔤 **P3 缩进已核 + 三处渲染缺陷已修（2026-10-15 14:25）** —— 段首缩进**正常且一致**"
           "（像素实测：顶格 458 行 = 标题下首段；缩进 36 行 ≈ 11 pt），标题下首段不缩进属 Elsevier 标准。"
           "修掉：① 定理头缺空格（原 `Theorem III.1(Representation Theorem).` ⇒ 自定义 `\\newtheoremstyle`，"
           "头后间距 5pt、正文正体，**编号方式不变**）；② `\\label{lem:r3-not-r3p}` **重复贴在定义与引理上**"
           "⇒ 定义改用 `def:gap-susceptibility`；③ `hyperref` 未设 `hidelinks` ⇒ 满页**绿色链接框**（实测 2224 像素 → **0**）。"
           "三份主稿变体（`main`/`main_full`/`main_10pp`）同步改；重编 **main 10 页 / supplementary 5 页，0 错误 0 未定义引用**；"
           "替换件已刷新。⚠️ **未改**：`Corollary 1–5` 实为 `\\subsection` 标题（打印成 `III.D. Corollary 1: …`）、"
           "`Lemma III.1.1` 的三级编号——两者都牵动补充材料里手写编号，**待操作者指示**。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 14:25 条目。\n")
    anchor = "21. 🗂️ **P3 替换件已按正常文件名备好（2026-10-15 14:15）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
    else:
        print("  WARN: map item 21 not found")

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("段首缩进", "Theorem III.1 (Representation Theorem)", "hidelinks", "lemma", "未改"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
