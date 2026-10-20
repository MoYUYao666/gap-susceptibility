# -*- coding: utf-8 -*-
r"""Record the P3 submission-status update (Required Reviews Completed, 2026-10-20) in the hand-off documents.

    python tools/_p1456_record_p3_reviews_completed.py --apply
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
PLAN = os.path.join(REPO, "docs", "UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md")

ENTRY = """> **📬 2026-10-20 22:50 —— P3（`PRLETTERS-D-26-02378R1`）状态变为 “Required Reviews Completed”**
>
> EM 实测行：`PRLETTERS-D-26-02378R1 | Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry |
> Oct 13, 2026（投）| Oct 20, 2026（状态变更）| **Required Reviews Completed**`。
>
> | 字段 | 值 |
> |---|---|
> | 稿件 | P3（`paper3/paper_ieee/`）|
> | 期刊 / 系统 | Pattern Recognition Letters / Editorial Manager |
> | 稿号 | `PRLETTERS-D-26-02378R1` |
> | 状态 | **Required Reviews Completed**（审稿意见已齐，等待编辑裁决）|
> | 变更时间 | 2026-10-20 |
>
> **含义**：审稿意见已全部回收，接下来是编辑决定（接收/小修/大修/拒）。修回件已备好：
> `paper3/paper_ieee/RESPONSE_TEMPLATE.md`（逐点回复骨架）、`cover_letter_prl_revision.{tex,pdf}`、
> 以及 10 页正文 + 6 页补充材料（含 S13 provenance）。**决定信一到**：按意见填模板 → 重编译 → 重建包
> （`SUBMISSION/_venue_builds/P3_PRL_next/`）→ 回复。
>
> 相关：P3 的本地升级（5-seed 统计、num-samples 消融）仍在跑，**不依赖本次决定**；若编辑要求补充证据，
> 这批结果可直接支撑回复。
>

"""

MAP_BLOCK = """> **📬 2026-10-20 22:50 状态更新（本块最新）**
>
> | 稿件 | 新状态 | 依据 |
> |---|---|---|
> | **P3** | **Required Reviews Completed（2026-10-20）** | Editorial Manager 状态行：`PRLETTERS-D-26-02378R1 ... Oct 20, 2026 Required Reviews Completed` |
>
> 旧条目中的“Decision in Process（2026-10-19）”**已过期**，以本块为准。修回件（response 模板 + cover letter +
> 10 页正文 + 6 页补充）已就绪，决定信到即可执行。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "2026-10-20 22:50" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "Required Reviews Completed（2026-10-20）" not in m:
        i = m.find("# 文件地图")
        if i < 0:
            i = m.find("# ")
        j = m.find("\n", i)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: j + 1] + "\n" + MAP_BLOCK + m[j + 1:])
        print("  file map updated")
    if os.path.exists(PLAN):
        p = io.open(PLAN, encoding="utf-8").read()
        if "Required Reviews Completed" not in p:
            io.open(PLAN, "w", encoding="utf-8", newline="").write(
                p.rstrip() + "\n\n> **2026-10-20 22:50 状态**：`PRLETTERS-D-26-02378R1` → **Required Reviews Completed**\n"
                "> （Oct 20, 2026）；审稿意见已回收，等待编辑裁决。修回件（response 模板/cover letter/10+6 页包）已就绪。\n")
            print("  upgrade plan updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
