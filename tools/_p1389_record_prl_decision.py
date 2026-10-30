# -*- coding: utf-8 -*-
r"""Record the P3 status change to "Decision in Process" (PRLETTERS-D-26-02378R1).

Evidence: the operator pasted the Editorial Manager row
  PRLETTERS-D-26-02378R1  Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry
  Oct 13, 2026 | Oct 19, 2026 | Decision in Process

    python tools/_p1389_record_prl_decision.py [--apply]
"""
from __future__ import annotations

import argparse
import io

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
WHICH = "哪篇是哪篇.md"
AUTO = "AUTOMATION_HANDOVER.md"
FOLLOW = "docs/SUBMISSION_FOLLOWUP_2026-10-19.md"

ENT = """> **⏳ 2026-10-20 07:10 —— P3（`PRLETTERS-D-26-02378R1`）状态变为 “Decision in Process”**
>
> EM 实测行：`PRLETTERS-D-26-02378R1 | Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry |
> Oct 13, 2026（投）| Oct 19, 2026（状态变更）| **Decision in Process**`。
>
> | 字段 | 值 |
> |---|---|
> | 稿件 | P3（`paper3/paper_ieee/`）|
> | 期刊 / 系统 | Pattern Recognition Letters / Elsevier EM |
> | 稿号 | **`PRLETTERS-D-26-02378R1`** |
> | 投出 | 2026-10-13 |
> | 状态变更 | **2026-10-19 → Decision in Process**（编辑正在做决定；审稿意见阶段已结束或接近结束）|
> | 官方截止 | 2026-11-02（R1 审稿期限，仍以 EM 实际为准）|
>
> **含义（不推测结果）**：EM 的 "Decision in Process" 表示审稿意见已齐、编辑正在裁决，可能结果依
> 常见流程为：接收 / 小修 / 大修 / 拒稿——**具体以邮件为准**，本文件不做猜测。
>
> **已备好的三种应对**：
> 1. **小修/大修**：本地工作副本已是"升级版"（10 页，含 [5,6] 重跑、seed 检查、补充材料 S11/表 S7、本地 CLIP
>    控制；Commentary→不适用），修回时从 `paper3/paper_ieee/` 重建提交包，引用 v2.0 归档（`RELEASE_NOTES_v2.0.md`）；
> 2. **接收**：按 PRL 要求提交最终源文件；把 `SUBMISSION/_venue_builds/P3_PRL_next/` 作为最终包基础，并在
>    Data availability 里保留 v1.0 版本 DOI、可选加 v2.0 版本 DOI；
> 3. **拒稿**：保留 v2.0 归档，按 `docs/UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md` 的已完成项直接改投，
>    无需重跑实验。
>
> 冻结纪律：已投出的 `SUBMISSION/P3_PRL_revision/UPLOAD_*` 与 `_frozen_submitted/` **不动**；等待邮件。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    changed = 0

    h = io.open(HANDOFF, encoding="utf-8").read()
    old = ("> | **P3** | Pattern Recognition Letters | `PRLETTERS-D-26-02378R1` | 🔄 **在审**：R1 于 2026-10-13 投出，"
           "替换件 2026-10-15 已发；**截止 2026-11-02** |")
    new = ("> | **P3** | Pattern Recognition Letters | `PRLETTERS-D-26-02378R1` | ⏳ **Decision in Process**"
           "（2026-10-19 状态变更；R1 于 2026-10-13 投出；官方期限 2026-11-02）|")
    if old in h:
        h = h.replace(old, new, 1)
        changed += 1
        print("  handoff table row updated")
    if "P3（`PRLETTERS-D-26-02378R1`）状态变为 “Decision in Process”" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        h = h[: j + 1] + "\n" + ENT + h[j + 1:]
        changed += 1
        print("  handoff entry added")
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h)

    m = io.open(MAP, encoding="utf-8").read()
    reps = [
        ("在审 **PRLETTERS-D-26-02378R1**、提交件冻结；审计 **72/98 PASS、0 WARN**；本地源已修 \\nabla/Overfull（提交件哈希未变，仍印 \"abla\"，下轮修）；**2026-10-18 编辑部回信：在审期间不接受替换件**（2 审稿人，1 完成 1 进行中）",
         "**PRLETTERS-D-26-02378R1**、提交件冻结；**2026-10-19 状态变为 Decision in Process（编辑裁决中）**；审计 **72/98 PASS、0 WARN**；本地源已修 \\nabla/Overfull；**2026-10-18 编辑部回信：在审期间不接受替换件**；本地升级稿（10 页 + supp 6 页）已就绪，若给修回可直接替换"),
        ("| **P3** | `paper3/paper_ieee/` | 正文 **10 页** | ✅ | **Under Review**（PRL `PRLETTERS-D-26-02378R1`）；替换件已备、**等编辑部回复** |",
         "| **P3** | `paper3/paper_ieee/` | 正文 **10 页** | ✅ | **Decision in Process**（2026-10-19；PRL `PRLETTERS-D-26-02378R1`）；**等编辑决定邮件**；修回包已备 |"),
        ("③ P3 等编辑部、下轮修 \"abla\"。",
         "③ P3 **Decision in Process**（2026-10-19），等决定邮件；若给修回，用本地升级稿（10 页 + supp）并重写 cover letter。"),
    ]
    for old, new in reps:
        if old in m:
            m = m.replace(old, new, 1)
            changed += 1
    row = ("120. ⏳ **P3 Decision in Process（2026-10-20 07:10）** —— PRL `PRLETTERS-D-26-02378R1` 于 **2026-10-19** 变为 "
           "Decision in Process（2026-10-13 投出；官方期限 2026-11-02）；三种结果应对已备（修回=本地升级稿 10 页+supp；接收=按最终源文件提交；"
           "拒稿=按已完成升级项直接改投）；冻结投出版与 `_frozen_submitted/` 未动；等邮件。\n")
    if "P3 Decision in Process（2026-10-20 07:10）" not in m:
        anchor = "119. 🚀 **Release v2.0"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
        changed += 1
    io.open(MAP, "w", encoding="utf-8", newline="").write(m)

    w = io.open(WHICH, encoding="utf-8").read()
    w = w.replace("**Under Review**（R1 2026-10-13 投；**2 审稿人：1 完成 1 进行中**；2026-10-18 编辑部回信：**在审期间不接受替换件**）",
                  "**Decision in Process**（2026-10-19 状态变更；R1 2026-10-13 投；此前 2 审稿人 1 完成 1 进行中；2026-10-18 编辑部回信：**在审期间不接受替换件**）", 1)
    w = w.replace("**Under Review**（R1 2026-10-13 投；2 审稿人：1 完成 1 进行中；**替换件请求被拒**，勘误留修订轮）",
                  "**Decision in Process**（2026-10-19；R1 2026-10-13 投；**替换件请求被拒**，勘误留修订轮）", 1)
    io.open(WHICH, "w", encoding="utf-8", newline="").write(w)

    a2 = io.open(AUTO, encoding="utf-8").read()
    a2 = a2.replace("### 2. P3（`paper3/paper_ieee/`）｜PRL `PRLETTERS-D-26-02378R1`（R1 已投，deadline 2026-11-02）",
                    "### 2. P3（`paper3/paper_ieee/`）｜PRL `PRLETTERS-D-26-02378R1`（R1 已投；**2026-10-19 Decision in Process**；deadline 2026-11-02）", 1)
    io.open(AUTO, "w", encoding="utf-8", newline="").write(a2)

    f = io.open(FOLLOW, encoding="utf-8").read()
    f = f.replace("| P3 | Pattern Recognition Letters | `PRLETTERS-D-26-02378R1` | 在审（2 审稿人，1 完成 1 进行中）| deadline **2026-11-02** |",
                  "| P3 | Pattern Recognition Letters | `PRLETTERS-D-26-02378R1` | **Decision in Process**（2026-10-19）| deadline **2026-11-02**；等决定邮件 |", 1)
    if "2026-10-19（EM）**：P3 状态" not in f:
        f = f.rstrip("\n") + "\n\n- **2026-10-19（EM）**：P3 `PRLETTERS-D-26-02378R1` 状态变为 **Decision in Process**（2026-10-13 投出）。\n"
    io.open(FOLLOW, "w", encoding="utf-8", newline="").write(f)
    print("  changed files:", changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
