# -*- coding: utf-8 -*-
r"""记录 ap3 的处置结论（2026-10-05，操作者指出）：**ap3 已无可投路径**。

## 操作者的判断

> "ap3 估计是没法用了，因为 paper3（=P3）已经投了 PRL 呀"

**判断正确**，且本项目文档里早有这条隐患提示（`文件地图.md:40`）：
> ⚠️ 新查清：`paper_ap3/`（86 页）**含 P3 内容**（Representation Theorem／Generalized Flow
> Allocation／counterfactual）→ **若 ap3 变可投，须先处理与 P3（已在 PRL 送审）的重叠**

## 实测证据

| 关键词 | 在 `paper_ap3/sections/` | 在 `paper3/`（已投 PRL） |
|---|---|---|
| Representation Theorem | **9** | 3 |
| GFAP | **11** | 4 |
| Generalized Flow Allocation | 2 | 3 |

→ **ap3 与 P3 稿件共享同一套核心理论构件**，重叠**不是猜测，是实测**。

## 为什么 ap3 已无可投路径（穷举）

| P1 结果 | ap3 能否投 | 原因 |
|---|---|---|
| **接收** | ❌ | P1 内容已另行发表 → **ap3 失去意义**（本项目的既有决策分支①） |
| **拒稿** | ❌ | 红线解除，但 ap3 **含 P3 内容**，而 P3 正在 **PRL `PRLETTERS-D-26-02378` 送审** → **一稿两投**；去掉 P3 后等同 `paper合`（= P1+P2），**而 `paper合` 已在编且更完整** |
| **修回** | ❌ | 红线仍在，且 P3 重叠问题不变 |

**→ 三条分支都不通。**

## 与 `paper合` 的关系

- `paper合/` = **P1 + P2**，NC **43 页**，**本会话整改对象**，已通过投稿前审核（可投）。
- `paper_ap3/` = **P1 + P2 + P3**，Elsevier `elsarticle`，**86 页**，含 P3 理论构件。
- **"ap3 去掉 P3" 与 `paper合` 是同一范围**（P1+P2）——故 ap3 不再提供任何独特内容。

## 处置建议（待操作者确认）

| 方案 | 说明 |
|---|---|
| **A（推荐）** | **把 ap3 标为"已无路径"归档**，不再维护；工作线只保留 `paper合`（P1+P2）与 `paper3`（P3@PRL） |
| **B** | 保留 ap3 目录但**明确标注**：仅作 P1+P2+P3 的合并技术参考，**不可投**（含 P3，与 PRL 送审稿重叠） |
| **C** | 若 P3 被 PRL 拒 → **重新评估** ap3（届时 P3 归位，ap3 或可作为一个整体投出） |

**注**：C 是唯一可能让 ap3 复活的路径，但它**依赖 P3 被拒**这一未来事件；**当前不应围绕它做任何工作**。

    python tools\_docs_ap3_verdict.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **🗂️ 2026-10-05 —— ap3 已无可投路径（**操作者指出**：P3 已投 PRL，重叠不可避免）**
>
> 操作者判断："**ap3 估计是没法用了，因为 paper3（P3）已经投了 PRL 呀**" —— **判断正确。**
>
> ### 实测证据（重叠不是猜测）
>
> | 关键词 | `paper_ap3/sections/` | `paper3/`（已投 PRL） |
> |---|---|---|
> | Representation Theorem | **9** | 3 |
> | GFAP | **11** | 4 |
> | Generalized Flow Allocation | 2 | 3 |
>
> → ap3 与 P3 稿件**共享同一套核心理论构件**。本项目文档早有隐患提示
> （`文件地图.md:40`）："若 ap3 变可投，须先处理与 P3（已在 PRL 送审）的重叠"。
>
> ### 三条分支穷举：ap3 均不可投
>
> | P1 结果 | 能否投 ap3 | 原因 |
> |---|---|---|
> | 接收 | ❌ | P1 内容已另行发表，ap3 失去意义 |
> | **拒稿** | ❌ | 红线虽解除，但 ap3 **含 P3 内容**，而 P3 正于 **PRL `PRLETTERS-D-26-02378`** 送审 → **一稿两投**；去掉 P3 后**等同 `paper合`（P1+P2）**，而 `paper合` 已在编且更完整 |
> | 修回 | ❌ | 红线仍在，P3 重叠不变 |
>
> ### 关键结论
>
> **"ap3 去掉 P3" 与 `paper合` 是同一范围（P1+P2）** → ap3 **不再提供任何独特内容**。
>
> | 稿件 | 范围 | 页数 | 状态 |
> |---|---|---|---|
> | `paper合/` | **P1 + P2** | 43 | ✅ **在编主稿，已过投稿前审核** |
> | `paper_ap3/` | P1 + P2 + **P3** | 86 | ❌ **无可投路径**（含 P3，与 PRL 送审稿重叠） |
> | `paper3/` | **P3** | 11 | 🏃 已投 PRL `PRLETTERS-D-26-02378`（2026-09-26），Under Review |
>
> ### 处置（待操作者确认）
>
> - **A（推荐）**：ap3 标为"已无路径"**归档**，不再维护；工作线只留 `paper合` 与 `paper3`；
> - **B**：保留目录但**明确标注不可投**（作为 P1+P2+P3 的技术参考）；
> - **C**：**若 P3 被 PRL 拒** → 重新评估 ap3（P3 归位后 ap3 或可作为整体投出）。
>   **C 依赖未来事件，当前不围绕它做任何工作。**

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "ap3 已无可投路径" in t:
        print("  HANDOFF 已记录，跳过")
        return 0
    anchor = "> **✅ 2026-10-05 —— 最终确认"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("ap3 已无可投路径", "Representation Theorem", "一稿两投", "不再提供任何独特内容"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

        # 文件地图：在 ap3 条目上标注
        mp = REPO / "文件地图.md"
        m = io.open(mp, encoding="utf-8").read()
        note = ("\n> **🗂️ 2026-10-05 结论：ap3 已无可投路径，建议归档。** 原因：**含 P3 内容**"
                "（Representation Theorem 9 处、GFAP 11 处，与 `paper3/` 重叠），"
                "而 **P3 已于 2026-09-26 投 PRL `PRLETTERS-D-26-02378`** 并在审 → 投 ap3 即**一稿两投**；"
                "去掉 P3 后**等同 `paper合`（P1+P2，43 页，已在编）**。三条分支（接收/修回/拒稿）均不可投。"
                "**唯一复活路径**：P3 被 PRL 拒后重新评估——**依赖未来事件，当前不投入。**\n")
        if "ap3 已无可投路径，建议归档" not in m:
            m = m.rstrip() + note
            io.open(mp, "w", encoding="utf-8", newline="").write(m)
            m2 = io.open(mp, encoding="utf-8").read()
            assert "ap3 已无可投路径，建议归档" in m2
            print("  ✅ 文件地图.md 已标注")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
