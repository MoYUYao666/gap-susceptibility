# -*- coding: utf-8 -*-
r"""落账：P3（`PRLETTERS-D-26-02378`）状态日期刷新为 **Oct 06, 2026**（2026-10-06）。

## 操作者提供的 EM 记录

```
PRLETTERS-D-26-02378  Gradient Structure Laws as Predictors of PEFT Design:
                      Zero-Shot Cross-Architecture Rank Allocation
                      Sep 28, 2026   Oct 06, 2026   Under Review
```

## 与既有记录的差别

| 字段 | 既有记录 | 本次 | 处置 |
|---|---|---|---|
| Status 日期 | **Sep 30, 2026**（2026-10-01 操作者报告） | **Oct 06, 2026** | **刷新，追加落账** |
| Submitted | Sep 28, 2026 | Sep 28, 2026 | 一致（**口径差异已查清，见下**） |
| Status | Under Review | **Under Review** | **未变** |

## ⚠️ 关于 `Sep 28` 这个日期：**已查清，不是新矛盾**

本仓库记录 P3 提交时刻为 **2026-09-26 16:22**（依**投稿确认页**），
而 EM 列表的 `Submitted` 显示 **Sep 28**。**该差异先前已解释并留档**：

- `文件地图.md:46`：*"⚠️ 日期口径：EM 列表把 P3 的 Submitted 记为 **Sep 28**，
  本仓库按投稿确认页记为 **09-26 16:22**"*
- `HANDOFF.md:1413` 同结论；并指出**同现象在 A1 上也出现过**（记录 08-16 投，EM 显示 Aug 19）。

**→ 结论：EM 列表的该字段 ≠ 原始投稿时刻**（更像"完成技术检查/进入处理"的时点）。
**保留原始记录，另记列表口径，不覆盖。**

    python tools\_docs_p3_status_1006.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **📮 2026-10-06 —— P3（`PRLETTERS-D-26-02378`）状态日期刷新为 Oct 06, 2026**
>
> **来源：操作者报告**（EM 列表，未见截图 → **记为"操作者报告"，不写成"已核实"**）。
>
> | Title | Submitted | Status 日期 | Status |
> |---|---|---|---|
> | Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation | Sep 28, 2026 | **Oct 06, 2026** | **Under Review** |
>
> **与既有记录的差别**：先前记录的状态日期为 **Sep 30, 2026**（2026-10-01 由操作者报告），
> 现显示 **Oct 06, 2026** → **状态日期被刷新**；**状态本身未变（仍 Under Review）**。
>
> ### ⚠️ 必须说清的两点
>
> 1. **仍是 Under Review，不是决定** —— 状态日期刷新**不代表**任何接受/修回/拒稿结论；
>    刷新原因未知（可能是审稿人接受邀请、提交意见或系统更新）→ **不推测**。
> 2. **来源是操作者报告**，未见 EM 截图。
>
> ### 📌 `Sep 28` 这个 Submitted：**不是新矛盾，先前已查清**
>
> 本仓库记录 P3 提交时刻为 **2026-09-26 16:22**（依**投稿确认页**），EM 列表 `Submitted` 显示 **Sep 28**。
> 该差异**已于 2026-10-01 解释并留档**（`文件地图.md:46`、`HANDOFF.md:1413`）：
> **EM 列表的该字段 ≠ 原始投稿时刻**（更像"完成技术检查/进入处理"的时点）；
> **同现象在 A1 上亦出现**（记录 08-16 投，EM 显示 Aug 19）。
> **→ 保留原始记录，不覆盖。**
>
> ### 影响面
>
> **无动作可做**（P3 在审期间不改稿、不催办，与既定策略一致）。
> **唯一关联**：`paper_ap3/` **因含 P3 内容而不可投**（P3 在审 → 合并投出构成重复投稿），
> 该结论**不变**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    # ── HANDOFF：追加新条目
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "P3（`PRLETTERS-D-26-02378`）状态日期刷新为 Oct 06" in h:
        print("  HANDOFF 已记录，跳过")
    else:
        anchor = "> **🆕 2026-10-01 —— PRL 两篇均进入 Under Review（已送外审）**"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENT + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("Oct 06, 2026", "状态本身未变（仍 Under Review）",
                  "不是新矛盾", "2026-09-26 16:22"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")

    # ── 文件地图：在 P3 行的日期口径说明处补记本次刷新
    fp = REPO / "文件地图.md"
    t = io.open(fp, encoding="utf-8").read()
    old = "> **稿件号 `PRLETTERS-D-26-02378`**（✅ 2026-09-28 落账，此前标\"待补\"）。"
    if "状态日期刷新为 Oct 06, 2026" not in t and old in t:
        t = t.replace(old, "> **稿件号 `PRLETTERS-D-26-02378`**（✅ 2026-09-28 落账，此前标\"待补\"）。\n"
                           "> 📮 **2026-10-06 状态日期刷新为 Oct 06, 2026**（仍 **Under Review**；"
                           "来源：操作者报告 EM 列表）——详见 `HANDOFF.md` 同日条目。", 1)
        io.open(fp, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(fp, encoding="utf-8").read()
        assert "2026-10-06 状态日期刷新为 Oct 06, 2026" in t2, "文件地图断言失败"
        print(f"  ✅ 文件地图.md 已补记（{len(t2.splitlines())} 行）")
    else:
        print("  文件地图：已记录或锚点未命中")

    # ── 哪篇是哪篇：状态日期同步
    wp = REPO / "哪篇是哪篇.md"
    w = io.open(wp, encoding="utf-8").read()
    if "Oct 06" not in w:
        w = w.replace("| `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | Under Review（09-26 投） |",
                      "| `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | Under Review（09-26 投；状态日期 10-06 刷新） |", 1)
        io.open(wp, "w", encoding="utf-8", newline="").write(w)
        print("  ✅ 哪篇是哪篇.md 已同步")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
