# -*- coding: utf-8 -*-
r"""Record the P3 correspondence fix (option A) in the handoff.

    python tools/_p894_record_p3_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "P3 正文↔补充材料对应关系已修好（方案 A）"

ENT = """> **✅ 2026-10-15 14:05 —— P3 正文↔补充材料对应关系已修好（方案 A：正文只动数字）**
>
> 操作者选定：**A**（重排补充材料使编号对齐，**正文的句子一字不改**）。
>
> ### 一、✅ 补充材料重排后的节号（按文件顺序）
>
> | 节 | 内容 | 正文引用它做什么 |
> |---|---|---|
> | S1 | Full Axiom Derivation of $\\Gamma$ | 公理推导 |
> | S2 | Experimental Details | 实验细节 |
> | S3 | GFAP Error Bound Derivation | 误差界推导 |
> | S4 | Detailed $\\Gamma$ Calculation for LLaVA-1.5-7B | 逐块耦合值 |
> | **S5** | **Rank Scaling and $\\Gamma$ Evolution** | 正文 **秩缩放** |
> | **S6** | **Decoder VLM**（含原 S9 的 summary）| decoder VLM 复现 |
> | **S7** | **Downstream Check on Real Image--Text Pairs**（含原 S9 的 summary）| 正文 **downstream check** |
> | S8 | Why $\\Gamma$ Transfers, and the Companion ODE Theory | 跨架构迁移 + 姐妹 ODE |
> | **S9** | **Deferred Proofs and Related Experimental Detail**（含 comparison / 样本量 / ShareGPT）| 正文 **样本量、第二数据集、与先前工作比较** |
>
> ### 二、✅ 正文只改了 **6 个数**（句子一字未动，`git diff` 可验）
>
> | 位置 | 原 | 新 |
> |---|---|---|
> | `main.tex` 补充材料小结 | `Supplementary Sections~S1--S6` | **`S1--S9`** |
> | `experiments.tex:187` 样本量稳健性 | `Section~S3` | **`Section~S9`** |
> | `experiments.tex:189` 第二数据集 | `Section~S3` | **`Section~S9`** |
> | `experiments.tex:420` 秩缩放 | `Section~S4` | **`Section~S5`** |
> | `experiments.tex:425` 与先前工作比较 | `Section~S5` | **`Section~S9`** |
> | `experiments.tex:297` downstream check | `Section~S7` | 不变（本就正确）|
>
> **实测 `git diff`：2 个文件、5 insertions / 5 deletions，全部是数字。**
>
> ### 三、✅ 补充材料内部 **8 处坏引用全部改成真 `\\ref`**
>
> | 原（印出来的样子）| 现 |
> |---|---|
> | `proof of **Theorem the main text**` | `proof of the Representation Theorem of the main text` |
> | `(**Lemma Lemma 1** of the main text)` | `Lemma~1 of the main text` |
> | `**Table the main text** reports the per-block values` | `Table~\ref{tab:gamma_detail}` |
> | `monotonically with rank (**Table the main text**)` | `Table~\ref{tab:gamma_rank}` |
> | `**Table Supplementary Table S4** compares GFAP` | `Table~\ref{tab:comparison}` |
> | `**Table Supplementary Table S3** reports` | `Table~\ref{tab:sharegpt}` |
> | `(**Figure Supplementary Figure S3**)` | `Figure~\ref{fig:ers}` |
> | `**Table Supplementary Table S2** shows the results`（**该表原本不存在**）| `Table~\ref{tab:samplesize}` |
>
> **并补上那张缺失的表**（`tab:samplesize`）：数据来自归档
> `paper3/scripts/outputs/experiments/sample_size_results.json`（**20 run、单 seed 999、4 epoch**），
> 逐格为 $\\Delta E$ 首末差：$n=16/64/128/256$ × $r=4,5,6,7,16$。
> **四个样本量都在 $r=5$→$r=6$ 之间变号**，与正文「crossing 稳定」一致。
> 表注**如实写明**：单 seed、4 epoch（此前正文与补充都只说"3 epochs"，**这是本轮另一处对不上的数字**，
> 表注按归档实况写）。
>
> ### 四、⚠️ 过程中踩到并修掉的三个坑（都记在脚本注释里）
>
> | # | 坑 | 后果 | 修法 |
> |---|---|---|---|
> | ① | `\\s` 被写成转义序列，落盘时**折叠成制表符** | 节标题正则**静默匹配 0 个**，脚本以为文件里没有节 | 所有 LaTeX 反斜杠改由 `chr(92)` 拼 |
> | ② | 我的新表 caption 里 `$` 不成对 | 编译 **Fatal error, no PDF** | caption 逐行断言 `$` 成对 |
> | ③ | 重建只由"节块"拼装 | **bibliography 与 `\\end{document}` 被丢掉** ⇒ `no legal \\end found` | 显式把末节之后的尾部原样接回 |
>
> ### 五、✅ 复核（两份都重编）
>
> | 项 | 结果 |
> |---|---|
> | `main.pdf` | **10 页 / 0 错误 / 0 未定义引用 / 0 未定义引文 / 0 `??`** |
> | `supplementary.pdf` | **5 页 / 0 错误 / 0 未定义引用 / 0 未定义引文 / 0 `??`** |
> | 补充表格 | 4 张 → **5 张**（TABLE S1–S5 号连续）|
> | 正文引用的 S 号 | **1、5、7、9**，逐个在补充里存在 |
> | 逐条对应校验 | `tools/_p893_p3_correspondence.py`：**5/5 OK，CORRESPONDENCE VERIFIED** |
> | 旧坏文本残留 | `Theorem the main text` / `Table the main text` / `Table Supplementary` / `Lemma Lemma` / `Figure Supplementary`：**全部 0** |
>
> ### 六、工具
>
> `tools/_p890_p3_supp_restructure.py`（重排 + 修引用 + 补表，幂等带断言）｜
> `tools/_p891_p3_main_pointers.py`（只改数字）｜
> `tools/_p892_p3_build_check.py`（两份日志审计）｜
> `tools/_p893_p3_correspondence.py`（从 PDF 逐条核对对应关系）。
>
> ⚠️ **PRL 侧**：`main.pdf` 与 `supplementary.pdf` 已随 10-13 的修订投出，本次为**新版本**，
> 建议**随下次修订/校样一并提交**。
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
    row = ("19. ✅ **P3 正文↔补充材料对应关系已修好（2026-10-15，方案 A）** —— 补充材料重排为 "
           "**S5=秩缩放、S6=Decoder VLM、S7=downstream check、S9=样本量/ShareGPT/与先前工作比较**；"
           "**正文只改 6 个数字**（`git diff` 5 insertions/5 deletions，句子未动）；补充内部 **8 处坏引用**"
           "改为真 `\\ref`，**并补上缺失的样本量表**（`tab:samplesize`，源自 "
           "`paper3/scripts/outputs/experiments/sample_size_results.json`：20 run、单 seed 999、4 epoch，"
           "四个样本量均在 $r=5\\to6$ 变号）。重编：**main.pdf 10 页 / supplementary.pdf 5 页，均 0 错误、0 `??`**；"
           "逐条对应 `tools/_p893_p3_correspondence.py` → **CORRESPONDENCE VERIFIED（5/5）**。"
           "⚠️ 两份 PDF 已随 10-13 修订投出，本次为新版本，建议随下次修订提交。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 14:05 条目。\n")
    anchor = "18. 🔍 **P3 正文↔补充材料对应关系已核（2026-10-15）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
    else:
        print("  WARN: map item 18 not found")

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("方案 A", "S1--S9", "tab:samplesize", "CORRESPONDENCE VERIFIED", "5 张"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
