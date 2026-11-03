# -*- coding: utf-8 -*-
r"""Record A1 novelty step 5: the framing (abstract, proposition placement, fourth finding) brought in line.

    python tools/_p1223_record_a1_framing.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

APPEND = """

---

# 第 5 步（2026-10-18 13:55）：框架补齐（摘要 / 命题位置 / 第四条发现）

此前正文是增量叠加的：摘要第一句与"Only the second"失去干净指代；引言仍写"三个受控实验、三条发现"，而实际已有第四条证据线。

## 改动

| 位置 | 改动 |
|---|---|
| 摘要 | **整段重写**（约 285 词）：先给"**非充分统计量**"结论与构造（33/52 点、200 方向控制 2.5 点），再给三骨干方向反转（+19.0/+19.4/+15.0）、gap surgery 塌缩、类对齐、任务敏感谱，最后以**一阶定律的量化边界**（保形 r=0.93–0.99、常数 0.36–0.98）收尾 |
| 引言 | "three controlled experiments" → **"four"**；新增**第 (iv) 条发现**：非充分性是结构性的（命题 + 匹配 gap 控制 + 三模型复现 + 相干性控制），并明确一阶场是"有边界的机制"而非预测律 |
| 命题位置 | 从 `\\input{related_work}` 之后移到**之前**（引言三条发现之后、相关工作之前），逻辑顺序正确 |

## 核验（`tools/_p1222_verify_a1_framing.py`）

```
abstract words (approx): 285
OK proposition occurrences = 1 ｜ OK abstract 'sufficient' = 1 ｜ OK finding (iv) = 1
OK proposition order: 7744 < related_work 8567 < Setup 8592
pages: 45 ｜ pdf: 'sufficient statistic' / 'four controlled experiments' / '0.36' / '0.98' 均在
```

A1 编译 **45 页**、**0 错误 / 0 未定义 / 0 Overfull**。

## 待办（选刊时处理）

摘要 285 词，多数 Elsevier 刊无硬限，但若新刊要求 ≤250 词需压缩；重排格式时按目标刊要求调整。
"""

ENT = """> **🧩 2026-10-18 13:55 —— A1 第 5 步：摘要/引言框架补齐（命题前置、第四条发现）**
>
> 摘要在增量叠加后出现指代断裂，已**整段重写**（约 285 词）：先给"gap **非充分统计量**"的结构性结论与构造
> （匹配 gap 差 33/52 点、200 方向控制仅 2.5 点），再给**三骨干方向反转**（CLIP +19.0 / OpenCLIP +19.4 / SigLIP +15.0）、
> gap surgery 塌缩、类对齐、任务敏感谱，最后落在**一阶定律的量化边界**（保形 r=0.93–0.99、常数 0.36–0.98）。
> 引言改为"**four** controlled experiments"，并新增**第 (iv) 条发现**；**命题**从 related_work 之后移到**之前**。
> A1 编译 **45 页**、0 错误 / 0 未定义 / 0 Overfull（校验脚本 `_p1222`，全 OK）。
> ⚠️ 摘要 285 词：多数刊无硬限，若新刊要求 ≤250 需压缩；待定刊后按格式重排。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    d = io.open(DOC, encoding="utf-8").read()
    if "第 5 步（2026-10-18" not in d:
        io.open(DOC, "w", encoding="utf-8", newline="").write(d.rstrip("\n") + APPEND)
        print("  doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 第 5 步" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("70. 🧩 **A1 第 5 步：摘要/引言框架补齐（2026-10-18 13:55）** —— 摘要整段重写（285 词，先给非充分性 + 构造 + "
           "三骨干反转 + 量化边界）；引言 `three→four controlled experiments` 并加第 (iv) 条发现；非充分性命题移到 "
           "related_work 之前。A1 **45 页**、0/0/0；校验 `_p1222` 全 OK。摘要 285 词待定刊后按需压缩。\n")
    if "A1 第 5 步" not in m:
        anchor = "69. 🧪 **A1 第 4 步"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
