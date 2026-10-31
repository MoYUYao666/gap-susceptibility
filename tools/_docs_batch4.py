# -*- coding: utf-8 -*-
r"""落账：task-6 结果改稿 + 我自身错误的修正（2026-10-12）。

    python tools\_docs_batch4.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📐 2026-10-12（续）—— task-6（LoRA/Adapter 的 lr 扫描）结果改稿；并修正本阶段我自己引入的 4 个错**
>
> ### task-6 结论：**各自调优后，LoRA 与全量微调不可区分**（R1.6 的实质答案）
>
> `outputs/analysis/pr_peft_lr_sweep.json`（**24 run / 2 seed / 0 失败**，`tools/_p291`）
>
> | 配置 @ lr | zero-shot top-1 | ΔCG |
> |---|---|---|
> | frozen | 59.91% | — |
> | **LoRA-both @ 1e-5（其最优）** | **60.69 ± 0.05%** | **−0.0054** |
> | **full-FT @ 1e-6（其最优，task-5）** | **60.87 ± 0.21%** | −0.0016 |
> | LoRA-text @ 3e-4 | 51.48 ± 1.08% | **−0.0469**（代价 8.4 点） |
> | Adapter-both @ 1e-5 | **0.13%** | +0.411 |
> | Adapter-both @ 3e-4 | 23.38% | +0.071 |
>
> **→ 差 0.18 点（落在 full-FT 自身 seed 波动内）与 0.004 ΔCG → 不可区分。**
> **→ 三族对 lr 响应方向相反**（full-FT 最优 1e-6、LoRA 1e-5、Adapter 要 ≥1e-4）
> → **单一共享 lr 不可能对三者公平**。
> **→ 论文建议已重述**：LoRA 的优势在**成本**与**检索**，**不在**"更保护对齐"。
> 代码级证明：`runs[*].peft_proof`（非 PEFT 参数全部 `requires_grad == False`；
> `n_trainable` = 491,520 / 196,608，**与论文 strict-freeze 数字完全一致**）。
>
> ### 关于 task-6 报的"Adapter 插入即破坏"——**不是新缺口**
>
> 队友测到 Adapter 的 `up.bias` 非零 → 插入即把 CG 推 +0.4460、R@1 掉到 0.0010。
> **复核结论**：论文**早已处理**——`validation.tex:126` 明写
> *"the earlier convention … would have shown the text-only Adapter as a reduction of $0.217$
> and **must not be compared with the LoRA figures**. On this common scale the Adapter's
> text-only arm does *not* improve …"*；且仓库已有 `outputs/analysis/adapter_common_baseline.json`
> 记录两种约定（`dCG_old_mean = −0.1155` vs `dCG_common_mean = +0.1848`）。
> **→ 记为"独立复现"，非新缺口。** 本阶段未改稿。
>
> ### ⚠️ 本阶段我自己引入并已修正的 4 个错（如实留档）
>
> | # | 错 | 后果 | 修法 |
> |---|---|---|---|
> | 1 | PowerShell 内联 here-string 写 LaTeX 时 `$` 被吞 | Springer 摘要 **4 处 `Missing $ inserted`** | `_p274` 整段重写 |
> | 2 | 把 `\\item` 插进 `discussion.tex` 的**散文**小节 | **`Lonely \\item`**（两版各 1 错） | `_p286` 改散文 |
> | 3 | `_p305` 的替换串写成 `\\$R^2\\$`（应为 `$R^2$`） | **NC 4 错 / Springer 2 错** | `_p306` 批量还原 |
> | 4 | **压摘要到 250 词时把混合效应 `\\beta=-0.95\\pm0.08` 删掉了** | 全稿 **0 处**——而这是审稿人 R1.2 明确要的东西 | `_p307` 加回并重压至 **250 词** |
>
> **并修掉一个**方法性**隐患**：`_p290` 审计脚本用字面 `in` 匹配 LaTeX 源，
> 而稿里句子**跨行**（~95 字符换行）→ **两次误报"缺失"**（`six dataset × backbone cells`、
> 混合效应）。现 `C()` 已**先归一空白再匹配**（`_p308` 为同一教训的独立复核脚本）。
>
> ### 同时查实的一处数字错（不改稿，仅记录）
>
> `highlights_nc.tex` 原称 *"median R2 of 0.97"*，归档 `ode_ledger.json::subsets.lora.median`
> = **0.9565** → 应为 **0.96**。已改为 0.96。
> **另更正一条我先前的错判**：*"88 of 94 无归档"* —— **有**，
> `outputs/analysis/monitor_dg_check2.json::rules."R1 平台化(ε=1%)"`（n=94, better=6, worse=88, same=2）。
> 误判原因：写作面只搜英文关键词，而该 JSON 的 key 是**中文** `平台化`。**已把归档路径写进正文。**
>
> ### 当前状态
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull | 摘要词数 |
> |---|---|---|---|---|---|
> | `main_nc` | **60** | 0 | 0 | 0 | **250** |
> | `main_springer` | **43** | 0 | 0 | 0 | **250** |
> | 投稿包 | **60** | 0 | 0 | — | — |
>
> **PR 核验 `tools/_p290_final_pr_audit.py`：26/26 通过。**
>
> ### 仍在跑（GPU 串行）
>
> - **task-7**：更低 lr（1e-7/3e-7）+ 高 lr 补 seed（成员 causal-hardener）
> - **task-8**：DINOv2 非对比式 backbone + 更大 VLM（成员 model-coverage）
>
> ⚠️ **task-8 的诚实预判**：DINOv2 部分可做；**LLaVA-7B 很可能不可行**（需 4-bit，
> 而本项目已证 4-bit 不可复现 → 禁止用作证据）。已要求队友**放不下就如实报"不可行 + 实测显存"**。
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "task-6（LoRA/Adapter 的 lr 扫描）结果改稿" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("task-6（LoRA/Adapter 的 lr 扫描）结果改稿", "60.69", "0.13%", "Lonely",
              "adapter_common_baseline", "monitor_dg_check2", "26/26"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
