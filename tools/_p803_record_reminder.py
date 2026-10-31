# -*- coding: utf-8 -*-
r"""Record the widened literature reminder and the paper roster.

    python tools/_p803_record_reminder.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔁 2026-10-15 19:00 —— 每周文献检索定时任务已从「只 Paper A」扩到「全部 6 篇稿件」**（操作者指出）
>
> ### 一、操作者指正
>
> > **"每周文献检索定时任务是指所有paper的相关新论文都检索，不是单单paper合，修改，继续完成"**
>
> **⇒ 原文确实只覆盖 Paper A**（标题即 `每周文献检索：Paper A 相关的竞争/可引用新论文`）。已改。
>
> ### 二、✅ 任务已改为覆盖 6 篇（`schedule-7342612c`，每周一 06:00 Asia/Shanghai）
>
> **新标题**：`每周文献检索：全部 6 篇稿件的竞争/可引用新论文`
>
> **清单来源**：`tools/_p802_paper_roster.py`（可从仓库重新生成，不靠记忆）
>
> | # | 稿件 | 目录 | 识别号 | 状态 | 专属必搜问题 |
> |---|---|---|---|---|---|
> | 1 | **Paper A** | `paper合/` | 无（目标 Neurocomputing）| **未投** | 间隙 ODE/梯度流、位置效应的架构依赖、降间隙≠提检索、WIT vs LAION、**冻结基座 LoRA 下的位置效应** |
> | 2 | **P3** | `paper3/paper_ieee/` | **`PRLETTERS-D-26-02378R1`** | **R1 已投**（deadline **2026-11-02**）| 零样本 rank 分配、能量-秩阈值 `r_c`、跨架构迁移、已撤回主张的再检验 |
> | 3 | **A1** | `paper_a1/` | **`NEUNET-D-26-09426`** | ATS 转投邀请（**2026-11-08** 前确认）| 间隙**不是**通用健康指标的反对方、保序性度量 |
> | 4 | **A23** | `paper_a2/` | **`26-0663`**（IEEE JOE）| **在审** | 非图像-文本模态对（声呐/音频-视觉）、gap-surgery 式诊断 |
> | 5 | **P1** | `paper/` | **`PR-D-26-10149`** | **已拒**（保底改投）| text-only 保对齐的竞争面 |
> | 6 | **ap3** | `备选/06_归档稿件/paper_ap3/` | — | 归档（仅合并参考）| — |
>
> ### 三、检索式结构（17 条，按稿件分节）
>
> - **跨稿通用 4 条**：PEFT×modality gap、text-only vs vision-only、adapter placement、cross-modal alignment theory
> - **Paper A 5 条**：gap 动力学/ODE、WIT vs LAION、gap↔retrieval 可分离、架构依赖、**冻结基座 LoRA 的适配位置**
> - **P3 4 条**：零样本 rank 分配、能量-秩阈值、跨架构迁移、免搜索的预算分配
> - **A1/A23 4 条**：gap 健康指标反例、保序性、声呐-视觉对齐、非图文模态对的诊断
>
> ### 四、保留并强化的纪律
>
> | 项 | 内容 |
> |---|---|
> | **引用必须真实** | Crossref / OpenAlex / arXiv abs / CVF / OpenReview 核实，记 DOI 或官方 URL |
> | **不得凭标题推断** | 必须读摘要（曾误判 `2609.17572` 实为博物馆偏见审计）|
> | **先查 `.bib`** | Paper A **94** 条 / P3 **63** 条 / P1 **45** 条（曾把已引用的 `zhang2026imod` 当新发现）|
> | **无预印本不编 DOI** | 只写可核实字段 |
> | 🆕 **跨稿合并** | 一条候选可标注**多稿受益** |
> | 🆕 **deadline 优先级** | 总评须指出**最紧急的一篇**（P3 11-02 > A1 11-08）|
>
> ### 五、下一步（继续完成）
>
> 1. **Paper A 的 rank 消融重跑**（`r ∈ {2,4,8,16,32,64}`，冻结基座的真 LoRA）—— 论文的 rank 主张目前**无有效证据支撑**；
> 2. `flickr30k` 29 个 run 的同类重跑（Paper A 的 ODE 拟合基于它们）；
> 3. **发布库同步**（`src/lora.py` + `src/trainer.py` 的修复）—— 待操作者确认。
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
    if "每周文献检索定时任务已从" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("每周文献检索定时任务已从", "全部 6 篇稿件", "17 条", "多稿受益", "2026-11-02"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
