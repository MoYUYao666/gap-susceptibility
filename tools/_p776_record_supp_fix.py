# -*- coding: utf-8 -*-
r"""Record the supplementary heading fix.

    python tools/_p776_record_supp_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔧 2026-10-15 10:30 —— Paper 3 补充材料标题重复：**6 处已全部修掉****（操作者指出）
>
> ### 一、操作者指出
>
> > **"paper3补充材料的ABCD小标题有重复诶，检查一下"**
>
> ### 二、🔴 查出**两类**问题，共 6 处重复标题
>
> **第一类：逐字重复，相邻两行完全相同（4 处）** —— 纯属编辑残留：
>
> | 行号 | 标题 |
> |---|---|
> | **L291 / L292** | `\\subsection{Comparison with Prior Work}` |
> | **L318 / L319** | `\\subsection{Rank Scaling and $\\Gamma$ Evolution}` |
> | **L358 / L359** | `\\subsection{Second-Dataset Validation (ShareGPT)}` |
> | **L422 / L423** | `\\subsection{Sample Size Robustness}` |
>
> **⇒ 处理：删掉每组第二行**（`tools/_p773`，带"必须是相邻逐字相同"的断言）。
> 行数 **566 → 562**。
>
> **第二类：同名但内容不同（2 处）** —— **不是重复内容，是"完整版 vs 摘要版"**，我起初判为"正常"是**误判**：
>
> | 位置 | 内容 |
> |---|---|
> | **§7 `Deferred Experimental Detail`** | **完整版**（L444 `Decoder VLM`、L476 `Downstream check`，逐项详述）|
> | **§9 `Deferred Downstream and Probe Detail`** | **摘要版**（L509、L526），其正文**明确写** *"Supplementary Section~S7"* / *"S6"* 指向完整版 |
>
> **⇒ 处理：把 §9 的两节改名为 `Downstream check (summary)` / `Decoder VLM (summary)`**（`tools/_p773b`，只在最后一个 section 内替换并断言恰好 1 处）。
>
> **⚠️ 我自己的检测器一度误报**：`tools/_p774` 用**子串**匹配，把 `Downstream check (summary)` 也算作 `Downstream check` ⇒ 报 **DUPLICATE**。
> 改用**精确标题比对**（`tools/_p775`）后为 **0 重复**。
> **教训：标题查重必须用精确匹配，子串匹配会把"带后缀的同名"误报为重复。**
>
> ### 三、✅ 修改后的标题结构（29 → 25 个标题，全部唯一）
>
> ```
> §1 Full Axiom Derivation of Γ
> §2 Experimental Details              (3 subsections)
> §3 GFAP Error Bound Derivation
> §4 Detailed Γ Calculation for LLaVA-1.5-7B
> §5 Why Γ Transfers Across Architectures
> §6 Relationship to the Companion ODE Theory
> §7 Deferred Proofs                   (Proof 1/2/3)
> §8 Deferred Experimental Detail      (Comparison with Prior Work / Rank Scaling and Γ Evolution /
>                                        Second-Dataset Validation (ShareGPT) / Sample Size Robustness /
>                                        Decoder VLM / Downstream check)
> §9 Deferred Downstream and Probe Detail
>                                      (Downstream check (summary) / Decoder VLM (summary) /
>                                       Operating-point probe)
> ```
>
> ### 四、✅ 编译与验证
>
> | 检查 | 结果 |
> |---|---|
> | 编译 | **5 页 / 0 错误 / 0 未定义引用** |
> | 精确重复标题 | **0** |
> | 6 个受影响标题各出现次数 | 全部 **1** |
>
> ### 五、⚠️ 已投稿的补充材料**也带这个问题**（无法再改）
>
> | 文件 | 字节 | 重复标题数 |
> |---|---|---|
> | **`SUBMISSION/P3_PRL_revision/UPLOAD/..._Supplementary.pdf`（已随 R1 投出）** | 266,021 | **6** |
> | **本轮修复后重编译** | 267,377 | **0** |
>
> **⇒ 已投稿版本无法更改**（P3 的 R1 已提交）。**若 P3 进入下一轮，用修好的版本替换。**
> **本轮只改源码与本地 PDF，未动 `SUBMISSION/` 下任何已投文件。**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "Paper 3 补充材料标题重复" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("Paper 3 补充材料标题重复", "566 → 562", "(summary)", "子串", "266,021", "0"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
