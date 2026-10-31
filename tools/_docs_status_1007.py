# -*- coding: utf-8 -*-
r"""落账 2026-10-07 EM 状态快照 + **更正昨天（10-06）对 P3 的误读**（2026-10-07）。

## 操作者 2026-10-07 提供的 EM 记录（三行）

| 稿号 | 标题 | Submitted | Status 日期 | Status |
|---|---|---|---|---|
| `PR-D-26-10149` | Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models | Jul 24, 2026 | **Oct 06, 2026** | **Decision in Process** |
| `PRLETTERS-D-26-02402` | Allocation, not selection: comparability in parameter-efficient multimodal adaptation | Sep 28, 2026 | Sep 30, 2026 | **Under Review**（未变） |
| `PRLETTERS-D-26-02378` | Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation | Sep 28, 2026 | **Oct 06, 2026** | **Required Reviews Completed** |

## ⚠️ 两处需要更正/说明

### ① **更正**：我 2026-10-06 把 P3 记成 "Under Review" 是**读了滞后显示**

10-06 操作者给的该行 Status 写 **Under Review**，我据此落账。
**但 10-07 的记录显示同一状态日期（Oct 06, 2026）为 `Required Reviews Completed`**
→ **10-06 那次是滞后/未刷新的显示**，**不是状态真的变过**。

**→ 更正为：P3 自 2026-10-06 起为 `Required Reviews Completed`。**

### ② **P1 从 `Required Reviews Completed` → `Decision in Process`**

- 10-04 记录：Status 日期 `Oct 04, 2026`、状态 `Required Reviews Completed`
- 10-06 记录：Status 日期 `Oct 06, 2026`、状态 **`Decision in Process`**
- **含义**：**编辑正在做决定**（意见已收齐 → 编辑决策中）。**尚未出结果。**

## 🔓 对 paper_ap3 / paper合 的解锁关系（本次最重要）

既定触发条件（`文件地图.md`、`HANDOFF.md:2705`）：**ap3 的可投性 = P1 的结果**

| P1 结果 | ap3 | 说明 |
|---|---|---|
| **接收** | ❌ **失去意义** | P1 内容已另行发表 |
| **大修 / 小修** | ❌ 仍不可投 | 稿件仍在审 |
| **拒稿** | ⚠️ **红线解除，但 ap3 仍不可投** | **因含 P3 内容，而 P3 正于 PRL 在审** → 去掉 P3 后**等同 `paper合`（P1+P2）** |

**→ 关键洞察**：**即使 P1 被拒，`paper_ap3/` 依然不可投**（P3 重复投稿）。
**真正的可投对象是 `paper合/`（P1+P2，49 页，已就绪）。**

**P3 的推进因此变得相关**：P3 进入 `Required Reviews Completed` → **离决定更近**；
P3 一旦出决定，`paper_ap3` 的重复投稿问题也随之见了分晓（但无论结果，`paper合` 都可用）。

    python tools\_docs_status_1007.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **📮 2026-10-07 —— EM 状态快照（三行）｜P1 进入 `Decision in Process`**
>
> **来源：操作者报告**（EM 列表，未见截图 → **记为"操作者报告"，不写成"已核实"**）。
>
> | 稿号 | 标题 | Submitted | Status 日期 | Status |
> |---|---|---|---|---|
> | **`PR-D-26-10149`** | Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models | Jul 24, 2026 | **Oct 06, 2026** | **`Decision in Process`** |
> | `PRLETTERS-D-26-02402` | Allocation, not selection: comparability in parameter-efficient multimodal adaptation | Sep 28, 2026 | Sep 30, 2026 | `Under Review`（未变） |
> | **`PRLETTERS-D-26-02378`** | Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation | Sep 28, 2026 | **Oct 06, 2026** | **`Required Reviews Completed`** |
>
> ### ① **更正我 2026-10-06 的记录**：P3 不是 Under Review，是**滞后显示**
>
> 10-06 操作者所给该行 Status 为 `Under Review`，我据此落账；
> **但 10-07 的记录显示同一状态日期（Oct 06, 2026）为 `Required Reviews Completed`**
> → **10-06 那次是滞后/未刷新显示，状态并未真的变过**。
> **→ 更正：P3 自 2026-10-06 起即为 `Required Reviews Completed`。**
>
> ### ② P1：`Required Reviews Completed` → **`Decision in Process`**
>
> - 10-04：状态日期 `Oct 04, 2026`，`Required Reviews Completed`
> - 10-06：状态日期 `Oct 06, 2026`，**`Decision in Process`**
>
> **含义**：**意见已收齐 → 编辑正在做决定**。**尚未出结果**（既非接受，也非修回/拒稿）。
> **刷新原因不推测。**
>
> ### 🔓 解锁关系（本次最重要）
>
> 既定触发条件（`文件地图.md`、`HANDOFF.md:2705`）：**ap3 的可投性绑定 P1 的结果**。
>
> | P1 结果 | `paper_ap3/` | 原因 |
> |---|---|---|
> | **接收** | ❌ **失去意义** | P1 内容已另行发表 |
> | **大修 / 小修** | ❌ 仍不可投 | 稿件仍在审 |
> | **拒稿** | ⚠️ **红线解除，但 `paper_ap3/` 仍不可投** | **含 P3 内容，而 P3 在 PRL 在审** → 去掉 P3 后**等同 `paper合`** |
>
> **→ 关键洞察：即使 P1 被拒，`paper_ap3/` 依然不可投**（构成与 P3 的重复投稿）。
> **真正可投的对象是 `paper合/`（P1+P2，49 页，已就绪）。**
>
> **P3 的推进因此相关**：进入 `Required Reviews Completed` → 离决定更近。
> 但**无论 P3 结果如何，`paper合/` 都可用**。
>
> ### ⏭ 待操作者决定（未变）
>
> `paper合/` 的**目标刊**：`docs/PAPERA_VENUE_OPTIONS.md`。
> 阻塞项 = 候选刊 **Guide for authors PDF**（优先 **KBS、ESWA、CVIU**）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    # ── ① HANDOFF：更正昨天条目 + 追加今天条目
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()

    # 1a. 在 10-06 的 P3 条目里就地加"已更正"
    old6 = ("> **与既有记录的差别**：先前记录的状态日期为 **Sep 30, 2026**（2026-10-01 由操作者报告），\n"
            "> 现显示 **Oct 06, 2026** → **状态日期被刷新**；**状态本身未变（仍 Under Review）**。")
    new6 = ("> **与既有记录的差别**：先前记录的状态日期为 **Sep 30, 2026**（2026-10-01 由操作者报告），\n"
            "> 现显示 **Oct 06, 2026** → **状态日期被刷新**。\n"
            ">\n"
            "> **🔴 本条已更正（2026-10-07）**：当时据操作者所给 Status 记为\"**仍 Under Review**\"，\n"
            "> **但 10-07 的记录显示同一状态日期（Oct 06, 2026）为 `Required Reviews Completed`** →\n"
            "> **10-06 那条是滞后/未刷新的显示，状态并未真的变过**。\n"
            "> **→ 实际状态：P3 自 2026-10-06 起即为 `Required Reviews Completed`**（见 10-07 条目）。")
    if "🔴 本条已更正（2026-10-07）" not in h and old6 in h:
        h = h.replace(old6, new6, 1)
        print("  ✅ HANDOFF：10-06 的 P3 条目已就地更正")
    elif old6 not in h:
        print("  ⚠ HANDOFF：10-06 条目锚点未命中")

    # 1b. 追加今天条目
    if "2026-10-07 —— EM 状态快照" not in h:
        anchor = "> **📮 2026-10-06 —— P3（`PRLETTERS-D-26-02378`）状态日期刷新为 Oct 06, 2026**"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        h = h[:i] + ENT + "\n" + h[i:]
        print("  ✅ HANDOFF：已追加 10-07 状态快照")
    io.open(hp, "w", encoding="utf-8", newline="").write(h)
    h2 = io.open(hp, encoding="utf-8").read()
    for k in ("Decision in Process", "🔴 本条已更正（2026-10-07）",
              "即使 P1 被拒，`paper_ap3/` 依然不可投", "Required Reviews Completed"):
        assert k in h2, f"HANDOFF 断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 断言通过（{len(h2.splitlines())} 行）")

    # ── ② 状态总表更新
    old_tbl = "> | `PR-D-26-10149` | Pattern Recognition | **P1**（`paper/`） | Required Reviews Completed |"
    new_tbl = "> | `PR-D-26-10149` | Pattern Recognition | **P1**（`paper/`） | **`Decision in Process`**（10-06） |"
    h3 = io.open(hp, encoding="utf-8").read()
    if old_tbl in h3:
        h3 = h3.replace(old_tbl, new_tbl, 1)
        io.open(hp, "w", encoding="utf-8", newline="").write(h3)
        print("  ✅ HANDOFF：状态总表 P1 行已更新")
    old_p3 = "> | `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | Under Review |"
    new_p3 = "> | `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | **`Required Reviews Completed`**（10-06） |"
    h4 = io.open(hp, encoding="utf-8").read()
    if old_p3 in h4:
        io.open(hp, "w", encoding="utf-8", newline="").write(h4.replace(old_p3, new_p3, 1))
        print("  ✅ HANDOFF：状态总表 P3 行已更新")

    # ── ③ 文件地图 + 哪篇是哪篇
    for fp, reps in (
        (REPO / "文件地图.md", [
            ("**P3** | Gradient Structure Laws as Predictors of PEFT Design | IEEEtran",
             "**P3** | Gradient Structure Laws as Predictors of PEFT Design | IEEEtran")]),
        (REPO / "哪篇是哪篇.md", [
            ("| `PR-D-26-10149` | Pattern Recognition | **P1**（`paper/`） | Required Reviews Completed |",
             "| `PR-D-26-10149` | Pattern Recognition | **P1**（`paper/`） | **Decision in Process**（10-06） |"),
            ("| `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | Under Review（09-26 投；状态日期 10-06 刷新） |",
             "| `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | **Required Reviews Completed**（10-06） |")]),
    ):
        t = io.open(fp, encoding="utf-8").read()
        o = t
        for a, b in reps:
            if a in t and a != b:
                t = t.replace(a, b, 1)
        if t != o:
            io.open(fp, "w", encoding="utf-8", newline="").write(t)
            print(f"  ✅ {fp.name} 已更新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
