# -*- coding: utf-8 -*-
r"""落账：PR 意见在 `paper合` 上**全部改完**（2026-10-12）。

    python tools\_docs_pr_all_done.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-12 —— PR 对 P1 的**全部意见**已在 `paper合` 上改完（操作者："全改对"）**
>
> ### 全景：PR 说了什么 → 我们改了什么
>
> **AE 的定性**：*"severe numerical inconsistencies, flawed statistics, unsubstantiated causal
> claims and unreliable generalization … invalidate core findings"*。四条**全部逐条处理**：
>
> | AE 指控 | 处置 | 关键数字变化 |
> |---|---|---|
> | **数值不一致** | 根因查清 + 重跑统一 + 逐处改正 | 批次混杂（19 run 用 64）→ **统一 128，重跑 100 run**；**`+0.079` 张冠李戴**（出自 Route D α=64 / R@1=0.389）→ **改为 −0.064**；`43 on Flickr30k` → **49**（43+6=49≠55）；Springer 摘要 $R^2$ **0.986 → 0.949**（0.986 超过集合最大值 0.9773） |
> | **统计有缺陷** | **补做混合效应 + 聚类标准误 + 聚类 bootstrap + 留出** | 论文只报汇合 $r=-0.714$ → 现并报 **M4 $\\beta=-0.95\\pm0.08$（ICC 0.9449）**、**CR1 SE 0.29（$p=0.016$）**、**族聚类 bootstrap $[-0.89,-0.62]$**、**有效 $n\\approx9$**、**留出 $R^2$ 0.51→0.24**；并给出**对稿件有利**的 Mundlak 结果（**组内 $-1.07\\approx$ 组间 $-1.01$**，不是纯组间假象） |
> | **因果过度声称** | **补做匹配相对扰动实验**（426 条件） | 原称 vision 噪声退化 **2.6×** → 匹配相对扰动下**预算比 $0.91\\pm0.45$（5% 损伤）/ $0.99\\pm0.45$（10%）**，**与无差异不可区分**，且**方向随协议翻转（0.60 vs 2.47）**；原协议"同一 $\\sigma$"实际给 vision **大 $1.14\\times$** 的相对扰动 |
> | **概化不可靠** | 标题收窄 + 16 处概化句限定 + 明确 scope | 标题去掉 *"Protect, Don't Perturb"* 的处方暗示 → ***Adaptation Site and the Modality Gap…***（6 处同步） |
>
> ### 审稿人逐条（R1.1–R3.4）的处置
>
> | 意见 | 处置 |
> |---|---|
> | R1.1 数值不一致 + 配置对照 | ✅ 批次统一重跑；`+0.079` 改正；`tab:position_strict` 已有；数据集分层已加 |
> | R1.2 伪重复/混杂 → 组内+混合效应+聚类+留出 | ✅ **全部补做**（见上）；**Mundlak 证明不是纯组间假象** |
> | R1.3 噪声被称"直接因果" | ✅ **匹配相对扰动实验**（负结果）；噪声描述改为逐张量 $\\sigma\\,\\mathrm{std}(W_i)$ 并披露 LayerNorm 被注入（占 vision 注入 Frobenius **73.9%**） |
> | R1.4 跨架构概化过强 | ✅ 标题收窄 + 概化句限定 + **新增检索协议澄清段**（COCO $R@1=1/5000$ 即 chance；BLIP-1 是选择性解冻；ViT-L 近似随机） |
> | R1.5 zero-overhead 不实 / DG-ES 过早终止 | ✅ 两词在稿中 **0 处**；`discussion` 已把"监测"与"停止"分开并给负面证据（$88/94$ 更差，**已补归档注**） |
> | **R1.6 优化超参不公平** | ✅ **补做 lr 扫描（9 run / 5 个 lr）**：**"崩塌"是共享 lr=1e-4 的伪影**——$\\mathrm{lr}=10^{-6}$ 时 zero-shot **60.87±0.21%**（> 冻结 59.91）、**ΔCG −0.0016±0.0052**；损伤随 lr 在三个数量级上单调 |
> | R2.1 标题泛化 | ✅ 收窄（6 处，保留对前任稿标题的披露） |
> | R2.2 新颖性区分 | ✅ 新增 `\\subsection{What This Paper Adds}`（三条文献脉络 + 明确"我们多做的那一步"） |
> | R2.3 实验规模/现代 VLM | ⚠️ 已有 DTD/Food-101/iNat；**更大 VLM 未做**（如实列为限制） |
> | R2.4/R3.3 Visual Fragility 过度因果 | ✅ 9 处逐处限定；小节标题改为 *"…an Interpretation of Where the Adapters Sit, **Not** of a Fragile Tower"*；写入匹配相对扰动的负结果 |
> | R2.5 DG 监控过早终止 | ✅ 同 R1.5 |
> | R3.1 摘要/结论与表格不一致 + 稿号 | ✅ `+0.079`/`−0.064` 各自标明配置；稿号披露已补 |
> | R3.2 post hoc 非预测 | ✅ 留出 $R^2$ 0.51→**0.24** → 明确改称 **association** |
> | R3.4 检索协议 | ✅ 新增澄清段 + 逐行 $R@1$ |
>
> ### 三处**我自己引入又被查出的错**（如实记录）
>
> 1. 用 PowerShell 内联写 LaTeX 吞掉 `$` → Springer 摘要 4 处 `Missing $ inserted`（`_p274` 修）
> 2. 把 `\\item` 插进散文小节 → `Lonely \\item`（`_p286` 修）
> 3. **误判** *"88 of 94 无归档"*——实际**有**（`monitor_dg_check2.json::rules.R1`，n=94/worse=88），
>    写作面只搜英文关键词而漏了中文 key `平台化`。**已复核并把归档路径写进正文。**
>
> ### 编译与投稿包
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | `main_nc` | **60** | 0 | 0 | 0 |
> | `main_springer` | **43** | 0 | 0 | 0 |
> | 投稿包 `Manuscript.pdf` | **60** | 0 | 0 | — |
>
> ### 仍然开放的（已如实写入 limitation，未粉饰）
>
> - **R2.3**：更大/更新的 VLM 未做
> - **LoRA/Adapter 的 lr 未扫描** → "每个方法各自调优"的更强公平性检验仍开放
> - 最优 full-FT lr（1e-6）在网格**边界**，更低 lr 未测
> - `3e-5/1e-4/3e-4` **仅 1 个 seed**
>
> **证据**：`docs/PR_STATS_FIX.md`（475 行，253 条主张过门禁）｜`docs/PR_CAUSAL_FIX.md`｜
> `docs/PR_FAIRNESS_FIX.md`｜`docs/PR_WRITING_FIX.md`｜`outputs/analysis/pr_*.json`
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "PR 对 P1 的**全部意见**已在" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("全部意见**已在", "0.986 → 0.949", "60.87", "0.91", "Mundlak",
              "monitor_dg_check2", "73.9%", "adapters Sit"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
