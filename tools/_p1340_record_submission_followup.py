# -*- coding: utf-8 -*-
r"""Record the submission-follow-up page (2026-10-19): status snapshot + Snapp post-submission stages.

    python tools/_p1340_record_submission_followup.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **📮 2026-10-19 14:05 —— 投稿后续跟踪：A1 技术检查仍在进行；Paper A 已投待送审（记录 Snapp 官方流程）**
>
> 读取 Snapp 官方 "What happens after submission" 与门户实测状态，写入 `docs/SUBMISSION_FOLLOWUP_2026-10-19.md`：
>
> | 稿件 | 状态（实测）| 下一步 |
> |---|---|---|
> | **A1**（PAA）| **Submission received ✓ → Technical check in progress**（v1.0；Submission ID `0a4629f0-…adc8b`；审稿 PDF 58 页）| 等技术检查 / 编辑部指派；**PAA 稿号待邮件** |
> | **Paper A**（Neurocomputing）| **Submitted**（`NEUCOM-D-26-23760`，2026-10-18）| 等 EM 变 "With Editor" |
> | P3（PRL R1）| 在审（2 审 1 完成）| deadline **2026-11-02** |
>
> 官方流程已按阶段落表（Technical check → Editorial assignment → With editor → Peer review → Revision → Decision → Transfer Desk），
> 并写明每阶段我们该做什么、状态一变要改哪 5 处文档；修回件将从**本地工作副本**重建，冻结包与 `_frozen_submitted/` 不动。
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
    if "投稿后续跟踪：A1 技术检查仍在进行" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("106. 📮 **投稿后续跟踪（2026-10-19 14:05）** —— `docs/SUBMISSION_FOLLOWUP_2026-10-19.md`：A1 **Submission received → Technical check 进行中**"
           "（PAA 稿号待邮件）；Paper A **Submitted `NEUCOM-D-26-23760`**；Snapp 八个后续阶段与每阶段动作、状态变更需同步的 5 处文档；"
           "修回件从本地工作副本重建，冻结包不动。\n")
    if "投稿后续跟踪（2026-10-19 14:05）" not in m:
        anchor = "105. 🧪 **升级包审核轮"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
