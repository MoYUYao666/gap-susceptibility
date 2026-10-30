# -*- coding: utf-8 -*-
r"""落账 2026-10-07 晚状态更新：**P3 回到 `Under Review`**（2026-10-07 晚）。

## 操作者提供（EM 列表）

| 稿号 | 标题 | Submitted | Status 日期 | Status |
|---|---|---|---|---|
| `PRLETTERS-D-26-02378` | Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation | Sep 28, 2026 | **Oct 06, 2026** | **Under Review** |
| `PRLETTERS-D-26-02402` | Allocation, not selection: comparability in parameter-efficient multimodal adaptation | Sep 28, 2026 | **Sep 30, 2026** | Under Review（未变） |

## ⚠️ 关键：P3 的状态**变回来了**——这是独立事实，不是更正

**完整时间线**（同一 Status 日期 `Oct 06, 2026` 下出现过两种状态）：

| 时点 | 记录值 | 来源 |
|---|---|---|
| 10-01 | Under Review（Status 日期 Sep 30） | 操作者报告 |
| 10-06 | **Under Review** | 操作者报告 → 我据此落账 |
| 10-07 早 | **Required Reviews Completed** | 操作者报告（同一 Status 日期 Oct 06） |
| 10-07 早 | —— 我据此**更正**了 10-06 那条，判为"滞后显示" | 我的推断 |
| **10-07 晚** | **Under Review**（Status 日期仍 Oct 06） | **操作者报告（本条）** |

**→ 现在有同一状态日期下"Under Review ↔ Required Reviews Completed"两个方向各一次的观测。**

**两种解释，我不选边**：

1. **状态真的往返过**：EM 在收到某审稿意见后显示 `Required Reviews Completed`，
   随后因**需要补充意见 / 编辑退回 / 审稿人状态变化**而回到 `Under Review`；
2. **EM 列表字段在不同页/不同时刻显示不一致**（此前已确认该列表的 `Submitted` 字段
   与投稿确认页相差 2 天，即**该列表并非逐字可靠**）。

**→ 处置：保留全部观测、标注为"已观察到往返"，不做因果解释。**
**这也修正我 10-07 早"判为滞后显示"的推断——该推断无法确定。**

## 对 P1 的影响：**无**

P1（`PR-D-26-10149`）自 10-06 起为 **`Decision in Process`**，本次未提供其更新，**状态不变**。

## 对 `paper_ap3/` 的影响：**无**

ap3 因**含 P3 内容**而不可投——**P3 只要仍在审（现在正是 Under Review），该结论就不变**。

    python tools\_docs_status_1007_pm.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **📮 2026-10-07 晚 —— P3 状态**回到 `Under Review`**（同一状态日期下的**往返**，已观测两次）**
>
> **来源：操作者报告**（EM 列表，未见截图 → **记为"操作者报告"，不写成"已核实"**）。
>
> | 稿号 | 标题 | Submitted | Status 日期 | Status |
> |---|---|---|---|---|
> | **`PRLETTERS-D-26-02378`** | Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation | Sep 28, 2026 | **Oct 06, 2026** | **`Under Review`** |
> | `PRLETTERS-D-26-02402` | Allocation, not selection: comparability in parameter-efficient multimodal adaptation | Sep 28, 2026 | Sep 30, 2026 | `Under Review`（未变） |
>
> ### ⚠️ 这是**独立事实**，不是对 10-07 早那条的更正
>
> 同一 Status 日期（`Oct 06, 2026`）下，两种状态**各被观测到一次**：
>
> | 时点 | 观测 | 来源 |
> |---|---|---|
> | 10-06 | `Under Review` | 操作者报告 |
> | **10-07 早** | **`Required Reviews Completed`** | 操作者报告 |
> | **10-07 晚** | **`Under Review`** | 操作者报告（本条） |
>
> **→ 状态在 `Under Review` ↔ `Required Reviews Completed` 之间往返过一次。**
>
> ### 两种解释，**我不选边**
>
> 1. **状态真的往返**：EM 在收到某审稿意见后显示 `Required Reviews Completed`，
>    随后因**需要补充意见 / 编辑退回 / 审稿人状态变化**而回到 `Under Review`；
> 2. **EM 列表字段本身在不同时刻/不同页显示不一致**——
>    此前已确认该列表的 `Submitted` 字段与投稿确认页**相差 2 天**（Sep 28 vs 09-26 16:22），
>    即**该列表并非逐字可靠**。
>
> **🔴 这也修正了我 10-07 早的推断**：我当时把 10-06 那次判为"滞后显示"并据此更正，
> **现在看该推断无法确定**——出现了两个方向的观测，不能只采信一个。
> **保留全部观测，不做因果解释。**
>
> ### 对 P1 与 `paper_ap3/` 的影响：**均无**
>
> - **P1**（`PR-D-26-10149`）自 10-06 起为 **`Decision in Process`**，本次未提供更新 → **不变**；
> - **`paper_ap3/` 仍不可投**——它含 P3 内容，而 **P3 仍在审**（现在正是 `Under Review`）→ **结论不变**。
>
> ### 操作含义：**无动作**
>
> 在审期间不改稿、不催办（与既定策略一致）。
> **"是否出决定"不看状态字段，看是否收到决定邮件**——本次两条**都仍是 Under Review**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()

    # ① 就地标注 10-07 早那条（其推断已被推翻）
    old = "> **→ 更正：P3 自 2026-10-06 起即为 `Required Reviews Completed`。**"
    new = ("> **→ 更正：P3 自 2026-10-06 起即为 `Required Reviews Completed`。**\n"
           ">\n"
           "> **🔴 该更正已于 2026-10-07 晚被推翻**：操作者当日**晚**的 EM 记录显示同一状态日期"
           "（`Oct 06, 2026`）为 **`Under Review`** → **状态在同一日期下往返过**，"
           "故\"滞后显示\"的推断**无法确定**。**保留全部观测**，见 10-07 晚条目。")
    if old in h and "该更正已于 2026-10-07 晚被推翻" not in h:
        h = h.replace(old, new, 1)
        print("  ✅ HANDOFF：10-07 早的推断已就地标注被推翻")

    # ② 追加本条目
    if "2026-10-07 晚 —— P3 状态" not in h:
        anchor = "> **📮 2026-10-07 —— EM 状态快照"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        h = h[:i] + ENT + "\n" + h[i:]
        print("  ✅ HANDOFF：已追加 10-07 晚条目")
    io.open(hp, "w", encoding="utf-8", newline="").write(h)
    h2 = io.open(hp, encoding="utf-8").read()
    for k in ("回到 `Under Review`", "我不选边", "该更正已于 2026-10-07 晚被推翻", "看是否收到决定邮件"):
        assert k in h2, f"HANDOFF 断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 断言通过（{len(h2.splitlines())} 行）")

    # ③ 状态总表：P3 改回 Under Review（保留 Required Reviews 的标注）
    old_tbl = "> | `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | **`Required Reviews Completed`**（10-06） |"
    new_tbl = ("> | `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | "
               "**`Under Review`**（10-07 晚；10-07 早曾为 `Required Reviews Completed`——**同一状态日期下往返过**） |")
    h3 = io.open(hp, encoding="utf-8").read()
    if old_tbl in h3:
        io.open(hp, "w", encoding="utf-8", newline="").write(h3.replace(old_tbl, new_tbl, 1))
        print("  ✅ HANDOFF：状态总表 P3 行已更新")
    else:
        print("  ⚠ 状态总表 P3 行未命中")

    # ④ 哪篇是哪篇
    wp = REPO / "哪篇是哪篇.md"
    w = io.open(wp, encoding="utf-8").read()
    old_w = "| `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | **Required Reviews Completed**（10-06） |"
    new_w = ("| `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | "
             "**Under Review**（10-07 晚；10-07 早曾为 Required Reviews Completed，同一状态日期下往返过） |")
    if old_w in w:
        io.open(wp, "w", encoding="utf-8", newline="").write(w.replace(old_w, new_w, 1))
        print("  ✅ 哪篇是哪篇.md 已更新")
    else:
        print("  ⚠ 哪篇是哪篇.md 未命中")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
