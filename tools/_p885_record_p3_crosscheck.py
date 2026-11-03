# -*- coding: utf-8 -*-
r"""Record the P3 main-text/supplement correspondence audit.

The audit itself was done with tools/_p880.._p884; this writes the result into the handoff so the
defects are actionable rather than living in a chat reply.

    python tools/_p885_record_p3_crosscheck.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "P3 正文与补充材料对应关系已核"

ENT = """> **🔍 2026-10-15 14:00 —— P3 正文与补充材料对应关系已核：**引用的补充节号/表号与补充材料实际不符****
>
> 操作者指令：**「paper3的正文和补充材料检查检查是否都对应上了」**。
> 对象：`paper3/paper_ieee/main.tex`（10 页，已投 PRL `PRLETTERS-D-26-02378R1`）与
> `paper3/paper_ieee/supplementary/supplementary.tex`（**5 页**）。
>
> ### 一、⚠️ 结论：**不对应**。正文引用的 7 处补充对象里，**6 处对不上**，另有 7 处交叉引用是**坏文本**
>
> **实测**（源码 + 两份已编译 PDF 逐条比对）：
>
> | 正文说 | 补充材料实际是 | 判定 |
> |---|---|---|
> | `Supplementary Section~S3`（样本量稳健性）×2 | **S8** 的 "Sample Size Robustness" 子节 | ❌ 差 5 节 |
> | `Supplementary Section~S4`（秩缩放）| **S8** 的 "Rank Scaling and $\\Gamma$ Evolution" | ❌ |
> | `Supplementary Section~S5`（第二数据集/ShareGPT）| **S8** 的 "Second-Dataset Validation (ShareGPT)" | ❌ |
> | `Supplementary Section~S6`（decoder VLM）| **S8** 的 "Decoder VLM" + **S9** 的 "(summary)" | ❌ |
> | `Supplementary Section~S7`（downstream check）| **S8** 的 "Downstream check" + **S9** 的 "(summary)" | ❌ |
> | 文末 "Supplementary Sections **S1--S6**" | 补充材料共 **S1–S9** | ❌ |
> | （正文未引用 §S8 的 "Comparison with Prior Work"）| 该节在 **S8**，而正文的 S5 指的是 ShareGPT | ❌ 结构错位 |
>
> ### 二、🔴 补充材料内部有 **7 处坏交叉引用**（**已印在提交的 PDF 里**）
>
> 不是"编号漂移"，是**编号被替换成了文字**——`\\ref` 被删掉、数字丢了的痕迹：
>
> | 行 | 现在印出来的样子 | 应为 |
> |---|---|---|
> | 47 | `A. Step-by-step proof of **Theorem the main text**` | 主文定理（Representation Theorem）|
> | 122 | `**Table the main text** reports the measured per-block values` | 本补充的 Table S1（`tab:gamma_detail`）|
> | 154 | `all $|\\Gamma_k|$ grow monotonically with rank (**Table the main text**)` | 本补充的 Table S2（`tab:gamma_rank`）|
> | 293 | `**Table Supplementary Table S4** compares GFAP with existing methods` | 本补充的 `tab:comparison`（实际印成 **S3**）|
> | 361 | `**Table Supplementary Table S3** reports the results`（ShareGPT）| 本补充的 `tab:sharegpt`（实际印成 **S4**）|
> | 423 | `**Table Supplementary Table S2** shows the results`（样本量）| 该表**不存在**（补充共 4 表，样本量结果无表）|
> | 331 | `(Figure **Supplementary Figure S3**)` | **S3 图不存在**（补充仅 1 张图 `fig:ers`）|
> | 52 | `(**Lemma Lemma 1** of the main text)` | 重复词 |
>
> **⇒ 提交版 `supplementary.pdf` 第 1 页就印着 "proof of Theorem the main text"。**
>
> ### 三、根因
>
> 补充材料在 2026-10-13 的修订中**被整体换过一版、并新增了 S7–S9 三节**（`supplementary.tex.bak_p648` 等 6 个备份可查），
> 但**正文里的节号是硬编码文字**（`Supplementary Section~S3`），不是 `\\ref`；
> 补充内部同样**没有一条 `\\ref`**（实测：补充 `refs` 计数 = **0**，5 个 `\\label` 全未被引用）。
> **⇒ 两边一旦重排，所有编号同时失效，且编译器不会报错**（它们不是引用，是普通文本）。
> 两份文档各自编译：`main.log` / `supplementary.log` 均 **0 未定义引用、0 错误** —— **唯一的证据只能靠人/工具逐条比对**。
>
> ### 四、✅ 可选修法（**待操作者选**，都会改变已投件的排版）
>
> | 方案 | 做法 | 影响 |
> |---|---|---|
> | **A（推荐）** | **重排补充材料**使 S3=样本量、S4=秩缩放、S5=ShareGPT、S6=decoder VLM、S7=downstream，并把表重排成 S2/S3/S4 与正文一致 | **正文一字不改**（`main.tex` 与已投 10 页件保持原样），只改补充；补充内的坏引用顺手改成 `\\ref` |
> | B | 改正文的 5 处节号去迁就补充现状 | 要动**已投正文**，且 §S8 一节包含 6 个子节，编号会很别扭 |
> | C | 把补充内部与外部的交叉引用**全部改为 `\\ref` + 共享标签**（两文档同一 `.aux` 才能跨文档引用）| 最彻底，但需要改构建方式 |
>
> **⚠️ 共同前提**：`supplementary.pdf` 与 `main.pdf` **已随 10-13 的修订一起投给 PRL**。
> 任何修改都属于**新版本** ⇒ **建议随下一次修订/校样一并提交**，本次先备好改法（已记本节）。
>
> ### 五、新增审计工具（幂等，可重跑）
>
> | 脚本 | 作用 |
> |---|---|
> | `tools/_p880_p3_crosscheck.py` | 正文↔补充：节号、标签、共有数值 |
> | `tools/_p881_p3_logs.py` | 两份日志的未定义引用/引文/错误 + 标签定义位置 |
> | `tools/_p882_p3_supp_inventory.py` | 补充的节/表/图/标签清单 + 坏引用扫描 |
> | `tools/_p883_p3_broken_refs.py` | 每处坏引用的上下文与修复目标 |
> | `tools/_p884_p3_section_map.py` | 逐节内容映射 + 两侧全部编号引用清单 |
>
> ### 六、✅ 其余项均已对应
>
> * `main.log` / `supplementary.log` / `main_full.log`：**0 错误、0 未定义引用、0 未定义引文**；
> * 正文 10 页 = 投稿件；`main_full.pdf` 13 页为存档；
> * 数据声明、AI 声明、致谢、资助、利益冲突五节在 `main.tex` 中齐备；
> * 补充里 `\\cite` 的 `sharegpt2023` 等键在 `supplementary/references.bib` 中可解析。
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
        print(f"  would prepend {len(ENT.splitlines())} lines to HANDOFF.md")
        return 0

    i = hp.find("# 项目交接文档")
    j = hp.find("\n", i)
    hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("18. 🔍 **P3 正文↔补充材料对应关系已核（2026-10-15）** —— **不对应**：正文引用的 "
           "`Supplementary Section~S3/S4/S5/S6/S7` 与文末 \"Sections S1--S6\" **全部与补充实际不符**"
           "（实际内容集中在 **S8**，S1–S9 共 9 节）；补充内部另有 **7 处坏交叉引用**（编号被替换成文字，"
           "如 `proof of Theorem the main text`、`Table Supplementary Table S4`、`Figure Supplementary Figure S3`），"
           "**已印在提交版 `supplementary.pdf` 第 1 页**。根因：两侧编号全是硬编码文本、无一条 `\\ref`，"
           "重排后编译器不报错。**修法待操作者选**（推荐 A：重排补充、正文不动）。"
           "审计工具：`_p880`–`_p884`。详见 `HANDOFF.md` 顶部 2026-10-15 14:00 条目。\n")
    anchor = "17. 📚 **参考文献已核（2026-10-15）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
    else:
        print("  WARN: map item 17 not found; map not updated")

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("不对应", "Theorem the main text", "Supplementary Table S4", "S1--S6", "已印在提交版"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
