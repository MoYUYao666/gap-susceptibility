# -*- coding: utf-8 -*-
r"""把"每周文献检索"这个例行约定记进 HANDOFF.md（2026-10-02）。

## 为什么必须记

调度器里的提醒**只存在于会话状态**；换会话、换机器就没了。
项目规矩要求"投递类/约定类事实第一时间落账"——例行任务的**检索清单与核实纪律**尤其要落文件，
否则每周执行时口径会漂移（本项目已经发生过"把已有的 bib 条目误报为新论文"这类事）。

    python tools\_docs_add_weekly_litsearch.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "HANDOFF.md"

ENTRY = r"""> **🗓️ 2026-10-02 —— 建立例行约定：每周一 09:00 自动检索相关新论文**
>
> **调度**：`schedule-7342612c`（weekly，周一 09:00 Asia/Shanghai）。
> **目的**：确认是否出现**竞争性工作**（有人做了同样的事）或**值得引用**的新论文。
>
> **检索按本稿的五条核心主张逐条问"是否有人做了同样的事"**：
>
> | 本稿主张 | 要搜的问题 |
> |---|---|
> | 梯度流导出 Gap Susceptibility + 一阶 ODE | 是否已有人提出**间隙的动力学/微分方程模型**？ |
> | 严格冻结下 CLIP 上 text-only 更降间隙 | 是否有人报告同一结论、或**反例**？ |
> | SigLIP 上 both 更优（方向相反） | 是否有人观察过**位置效应的架构依赖**？ |
> | 降间隙 ≠ 提检索（三架构一致） | 是否有人论证间隙与检索**可分离**？ |
> | 位置效应依赖预训练数据（WIT vs LAION） | 是否有人把间隙归因于**预训练数据/信息不平衡**？ |
>
> **核实纪律（本项目三条教训，写死在提示里）**：
> 1. **引用必须真实**——每条用 Crossref / OpenAlex / arXiv abs / CVF / OpenReview 核实，记录 DOI 或官方 URL；
> 2. **不得凭标题推断内容**——必须读到摘要（教训：`2609.17572` 标题像"VLM 审计"，实为博物馆偏见研究）；
> 3. **先查 `paper合/references.bib`（41 条）**——教训：`zhang2026imod` 早已在 bib 且**已被引用**，
>    我却在 2026-10-02 的检索中把它当成"新发现"；正确做法是"补深度"而非"加条目"。
>
> **汇报格式**：每条候选三行（是什么 / 与本稿关系 / 行动），末尾三句总评。
> **若要改稿**：写 `tools/` 下带断言的幂等脚本 → 重编译两版 → 跑两个审计 → 按收尾规则同步三件文档。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    anchor = "> **🆕 2026-10-02 —— Paper A"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    print("  ✅ 找到锚点（插在 2026-10-02 主条目之前）")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("schedule-7342612c", "每周一 09:00", "2609.17572", "zhang2026imod"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ 已写入并断言通过（{len(t2.splitlines())} 行）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
