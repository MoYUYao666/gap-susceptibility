# -*- coding: utf-8 -*-
r"""按操作者 2026-10-12 澄清更新文档：**P1 已被 PR 拒稿**；**Paper A 从未投稿**（2026-10-12）。

## 操作者原话（2026-10-12）

> 「P1已拒稿，投的是PR，Paper A还没有投过，只需更新文档，不需要说些什么」

## 事实

| 稿件 | 事实 |
|---|---|
| **P1**（`paper/`，`PR-D-26-10149`） | 投 **Pattern Recognition**，**已拒稿**（此前文档记为 `Required Reviews Completed` / `Decision in Process`） |
| **Paper A**（`paper合/`） | **从未投稿**（任何期刊）。此前"受 P1 审稿期伦理约束"的表述**不再适用** |
| **ap3**（`备选/06_归档稿件/paper_ap3/`） | 因 P1 拒稿 → **重复投稿红线解除**；但**仍含 P3 内容**（P3 在 PRL 在审 `PRLETTERS-D-26-02378`）→ 与 P3 的重叠**仍须先处理** |

## 更新方式（遵循项目"追加不重写 + 标注过期"）

1. `HANDOFF.md`：顶部**追加**状态更正条目（历史条目保留）。
2. `文件地图.md`：顶部**追加**更正条目 + 就地修正状态表的两条过期表述。
3. 其余 `docs/*.md`：**不改**（它们是各自时点的记录，且 HANDOFF/文件地图已给出当前事实）。

    python tools\_p341_update_p1_rejected.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

HANDOFF_ENT = """> **🔴 2026-10-12 —— 状态更正（操作者澄清）：P1 已被 Pattern Recognition 拒稿；`paper合`（Paper A）从未投稿**
>
> **操作者原话**：「P1已拒稿，投的是PR，Paper A还没有投过，只需更新文档，不需要说些什么」
>
> ### 更正内容
>
> | 稿件 | 本文件此前所记 | **实际（2026-10-12）** |
> |---|---|---|
> | **P1**（`paper/`） | `PR-D-26-10149` = **`Required Reviews Completed`**（2026-10-04 状态刷新）／`Decision in Process`（2026-10-06） | 🔴 **已拒稿**（期刊 = **Pattern Recognition**） |
> | **`paper合`（Paper A）** | "就绪，但**受 P1 审稿期伦理约束**暂不能投" | 🔴 **从未向任何期刊投稿**（因此不存在"审稿期伦理约束"） |
> | **`paper_ap3/`** | "因含 P3 内容不可投；若 P1 拒稿则红线解除" | ✅ **P1 拒稿 → 重复投稿红线已解除**；但**仍含 P3 内容**（P3 在 PRL 在审 `PRLETTERS-D-26-02378`）→ **与 P3 的重叠仍须先处理** |
>
> ### 本文件历史条目如何读
>
> - 2026-10-01 / 10-04 / 10-06 / 10-07 各条关于 P1 处于 `Required Reviews Completed` /
>   `Decision in Process` / 状态往返的记录，**均为当时操作者报告的真实观测**，
>   **不删不改**——它们记录的是**决定到达之前**的状态序列。
> - 但**其结论部分（"等 P1 决定"这一待办）现已终结**：决定已到，结果是拒稿。
> - 凡本文件中「**受 P1 审稿期伦理约束**」「**唯一未决变量仍是 P1 的决定**」
>   「**等 P1 决定后投 Neurocomputing**」等表述，**自本条起均视为过期**。
>
> ### 其余三份在审稿件状态（未变，仍以操作者报告为准）
>
> | 稿号 | 期刊 | 是哪篇 | 状态 |
> |---|---|---|---|
> | `NEUCOM-D-26-20952` | Neurocomputing | A1（`paper_a1/`） | **桌面拒稿（2026-10-10）**；ATS 转投邀请须 **2026-11-08** 前确认 |
> | `PRLETTERS-D-26-02378` | Pattern Recognition Letters | P3（`paper3/`） | 在审 |
> | `PRLETTERS-D-26-02402` | Pattern Recognition Letters | 综述（`paper_review_prl/`） | 在审 |
> | `26-0663` | IEEE JOE | A23（`paper_a2/`） | Received（2026-09-21） |
>
> ### `paper合`（Paper A）当前就绪度（未变）
>
> | 项 | 值 |
> |---|---|
> | NC 版 | **60 页**，0 错误 / 0 未定义 / 0 Overfull |
> | Springer 版 | **44 页**，0 错误 / 0 未定义 / 0 Overfull |
> | 摘要 | **250 词**（Neurocomputing 限 250） |
> | 投稿包 `NC_submission/Manuscript.pdf` | **60 页**，已同步（zip 43 文件） |
> | PR 审稿意见处置 | **26/26** 核验通过（`tools/_p290_final_pr_audit.py`） |
> | 尚在跑 | task-7（更低 lr + 补 seed）｜task-8（DINOv2 非对比 backbone） |
> | **投稿状态** | **从未投稿** |
"""

MAP_ENT = """> **🔴 2026-10-12 —— 状态更正（操作者澄清）：P1 已被 PR 拒稿；`paper合` 从未投稿**
>
> - **P1**（`paper/`，`PR-D-26-10149`）**已拒稿**，期刊 = **Pattern Recognition**。
>   本文件此前记的 `Required Reviews Completed`（2026-10-04）/ `Decision in Process`（10-06）
>   是**决定到达之前**的状态，**不再有效**。
> - **`paper合`（Paper A）从未向任何期刊投稿**。凡本文件写"受 P1 审稿期伦理约束，暂不能投"的，
>   **自本条起过期**——约束不存在。
> - **`paper_ap3/`**：P1 拒稿 → **重复投稿红线解除**；但**仍含 P3 内容**（P3 在 PRL 在审），
>   **与 P3 的重叠仍须先处理**后方可考虑投出。
> - **`paper合` 当前就绪度**：NC **60 页** / Springer **44 页**，0 错误 / 0 未定义 / 0 Overfull；
>   摘要 **250 词**；投稿包 `NC_submission/Manuscript.pdf` **60 页**已同步；
>   PR 审稿意见 **26/26** 核验通过。**从未投稿。**
"""

# 就地修正（追加过期标注，不删原text）
FIXES = [
    ("文件地图.md",
     r"**受 P1 审稿期伦理约束，暂不能投**",
     r"**受 P1 审稿期伦理约束，暂不能投** ⚠️**此表述已于 2026-10-12 过期**：P1 已被 PR 拒稿，"
     r"约束不存在；`paper合` 从未投稿（但 ap3 仍含 P3 内容，与在审的 P3 重叠须先处理）"),
    ("文件地图.md",
     r"就绪，但**仍受 P1 审稿期伦理约束**；另有约 312 词与 P1 的重叠待清理",
     r"就绪，但**仍受 P1 审稿期伦理约束** ⚠️**2026-10-12 过期**：P1 已拒稿、约束不存在，"
     r"`paper合` 从未投稿；另有约 312 词与 P1 的重叠待清理（该清理仍应做）"),
]


def prepend(path: Path, ent: str, marker: str) -> bool:
    t = io.open(path, encoding="utf-8").read()
    if marker in t:
        print(f"  {path.name}: 已记录")
        return False
    i = t.find("\n")
    io.open(path, "w", encoding="utf-8", newline="").write(t[:i + 1] + "\n" + ent + "\n" + t[i + 1:])
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）—— 将执行：")
        print("    1. HANDOFF.md 顶部追加状态更正条目")
        print("    2. 文件地图.md 顶部追加状态更正条目")
        print(f"    3. 文件地图.md 就地标注 {len(FIXES)} 处过期表述")
        return 0

    hp = REPO / "HANDOFF.md"
    if prepend(hp, HANDOFF_ENT, "P1 已被 Pattern Recognition 拒稿"):
        print(f"  ✅ HANDOFF 已追加（{len(io.open(hp, encoding='utf-8').read().splitlines())} 行）")

    mp = REPO / "文件地图.md"
    if mp.exists():
        if prepend(mp, MAP_ENT, "P1 已被 PR 拒稿"):
            print("  ✅ 文件地图 已追加")
        t = io.open(mp, encoding="utf-8", errors="replace").read()
        n = 0
        for f, old, new in FIXES:
            if f != "文件地图.md":
                continue
            c = t.count(old)
            if c and "2026-10-12 过期" not in t[t.find(old):t.find(old) + len(old) + 120]:
                t = t.replace(old, new)
                n += c
        if n:
            io.open(mp, "w", encoding="utf-8", newline="").write(t)
            print(f"  ✅ 文件地图 就地标注 {n} 处过期表述")

    # 核对
    t2 = io.open(hp, encoding="utf-8").read()
    t3 = io.open(mp, encoding="utf-8").read()
    checks = {
        "HANDOFF 含 P1 拒稿": "P1 已被 Pattern Recognition 拒稿" in t2,
        "HANDOFF 含 Paper A 从未投稿": "**从未投稿**" in t2 or "从未向任何期刊投稿" in t2,
        "HANDOFF 含 ap3 红线解除": "重复投稿红线已解除" in t2,
        "文件地图 含 P1 拒稿": "P1 已被 PR 拒稿" in t3,
        "文件地图 含过期标注": "2026-10-12 过期" in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
