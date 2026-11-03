# -*- coding: utf-8 -*-
r"""落账：P3 收到 Revise（33 条）→ 选 C（全部补实验）；理论缺口已修（2026-10-12）。

    python tools\_p417_record_p3_revise.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📮 2026-10-12 —— P3（`PRLETTERS-D-26-02378`）收到 **Revise**：33 条意见，操作者选 **C（全部补实验）**
>
> ### 决定信息（从 `docs/_inbox/P3_reviews/` 的邮件与审稿 PDF 逐字提取）
>
> | 字段 | 值 |
> |---|---|
> | 期刊 / 稿号 | **Pattern Recognition Letters** ｜ **`PRLETTERS-D-26-02378`** |
> | 决定 | **Revise**（可修改后重审，非拒稿） |
> | 提交 / 状态日期 / **截止** | Sep 28, 2026 ｜ Oct 12, 2026 ｜ **Nov 02, 2026**（**逾期视为撤稿**） |
> | 编辑 | **Yonghuai Liu**（Editor-in-Chief） |
> | 总评 | *"clarity of technical details and **sufficiency of experimental studies**"* |
> | 平台要求 | **必须在 Editorial Manager 逐条 reply to reviews** |
>
> ### 意见量：**33 条**（R1 5 ｜ R2 5 ｜ R3 23），编号全部连续
>
> **⚠️ 我的解析工具第一版漏检**：用 `^|\n` 锚定编号 → **漏掉行末编号**
> （R2 报 3 条实为 5、R3 报 18 条实为 23）。改用「**编号必须连续**」作校验后修正。
> **本阶段"判据太窄"类错误第 14 次。**
>
> ### 33 条集中于 **10 个根问题**
>
> | 根 | 问题 | 出现于 | 类型 |
> |---|---|---|---|
> | **A** | 🔴 **`block additivity ⇒ bilinear` 证明有缺口**（`‖x‖²` 亦 block-additive） | R1.5, R3.3 | **理论必须改** |
> | **B** | 唯一性 vs「特定熵正则目标下的最优」未区分 | R1.3, R3.1 | 理论表述 |
> | **C** | 为何用 **\\|Γ\\|**（丢符号方向信息） | R1.3, R3.8 | 澄清 |
> | **D** | 正交重参数化假设 vs LoRA **非正交 A/B** | R2.5, R3.2, R3.3 | 澄清+限定 |
> | **E** | 🔴 **无真正的逐块 Γ 引导分配实验**（Theory 组用 uniform r=4） | R2.2, R2.4, R3.9, R3.21 | **需补实验** |
> | **F** | 🔴 **无下游评测**（只有 alignment energy） | R1.3, R2.3, R3.15, R3.16 | **需补实验** |
> | **G** | 🔴 **blank images + 小训练集**，非真实图文 | R1.4, R3.13, R3.14, R3.23 | **需补实验** |
> | **H** | 跨架构证据不足（只 LLaVA-1.5 + Qwen2-VL，**后者行为不同**） | R1.4, R3.10, R3.11 | **需补实验/改表述** |
> | **I** | 统计与可复现性（3 seeds、CI 跨零、30×、NaN 归因、软件版本） | R3.17–R3.22 | **需补统计/诊断** |
> | **J** | 零样本定义不清（是否真不访问目标模型梯度） | R2.1, R3.10 | 澄清 |
>
> ### ✅ 根问题 A 已修（`tools/_p416`，我亲自做）
>
> **审稿人是对的。** 我核到两处病处：
> 1. `appendix.tex` *"Full Axiom Derivation"* 第 1 步把 *"由 (AX3)，最一般的一阶泛函**是**双线性"* 当**断言**；
> 2. `theory.tex` 的 *"Why must Γ be bilinear?"* 段写 *"(R3) ⟹ f(x+y)=f(x)+f(y)"*，
>    **把 R3（块级分解可加）当成了自变量求和可加**；
>    而 R3 的定义 $S(M_a\\oplus M_b)=S(M_a)+S(M_b)$ 对 $\\|\\nabla E\\|^2$ **同样成立**。
>
> **修法（如实承认 + 显式补上 + 给反例）**：
> - 新增公理 **R3′（cross-block additivity）**，明确它**比 R3 强**
> - 新增 **Lemma**（`lem:r3-not-r3p`）+ **反例 $S=\\|x\\|^2$** 证明 R3 ⇏ R3′
> - 定理重述为「**在 R1–R5 加 R3′ 下唯一 up to 正缩放**」，并**如实标注 R3′ 是新增结构假设**
>   （**不是**从 R1–R5 推出）——这同时回应 **R3.1**（"R1–R5 是必要条件还是强加假设"）
> - `appendix` 第 1 步改为**承认缺口**并引用该 Lemma
>
> **编译：P3 `main.pdf` = 11 页（PRL 上限），0 错误 0 未定义** ✅
>
> ### 工作分解（三成员已开跑）
>
> | 任务 | 负责 | 内容 | 脚本编号 |
> |---|---|---|---|
> | **task-9** | `p3-allocation` | **E 组**：真逐块 Γ 引导分配（vs uniform/random，**同预算且断言参数量相等**）+ ≥2 既有方法同预算比较 + **完整逐块 Γ_k/rank 表**（R3.12） | `_p420`+ |
> | **task-10** | `p3-downstream` | **F+G 组**：**真实图文对复跑** rank transition 与 Γ 排序 + **≥1 下游指标** + blank vs 真实量化 | `_p430`+ |
> | **task-11** | `p3-stats` | **I 组**：bootstrap CI/MAD/最坏情况/显著性 + **可复现性分析** + **NaN 归因** + **Γ 的 batch 敏感性** | `_p440`+ |
>
> **已交付**：`docs/P3_REVIEW_RESPONSE.md`（应答工作文档，33 条逐条含建议动作与空回复块）｜
> `outputs/analysis/p3_reviews_parsed.json`（意见原文）｜`outputs/analysis/p3_review_classes.json`（分类）
>
> ### 给 `p3-stats` 的关键提示（本项目已查明的实质答案）
>
> `paper合` 的实验里查明：**评测画廊继承了训练用随机变换**（`create_dataloaders` 的
> `random_split` 保留 train transform）→ 同一 checkpoint 重复评测 **CG sd 0.00025 / R@1 sd 0.0055**。
> 这**正是 R3.18「环境敏感」的实质性答案之一**，远胜空谈版本号。已要求它核查 P3 是否走同一 loader。
>
> ### 尚未做（诚实标注）
>
> - **33 条回复的正式文本尚未撰写**（工作文档已就绪，需补实验数据后填充）
> - **F/G 组的规模受本机限制**：LLaVA-1.5-7B bf16 在 8 GB 上**不可行**（实测 13.157 GiB 权重）
>   → 已要求成员用小模型做，**做不了就如实报告并给主张降级建议**
> - 三成员的实验结果**尚未回来**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "P3（`PRLETTERS-D-26-02378`）收到 **Revise**" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("收到 **Revise**", "Nov 02, 2026", "lem:r3-not-r3p", "33 条", "task-11"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
