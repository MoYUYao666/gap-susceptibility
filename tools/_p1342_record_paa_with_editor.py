# -*- coding: utf-8 -*-
r"""Record the PAA status update of 2026-10-19: technical check and editorial assignment passed; the manuscript is now
"With editor".

Evidence: portal screenshot provided by the operator (status card "You have an editor assessing your submission"; progress
Submission received ✓ → Technical check ✓ → Editorial assignment ✓ → With editor (current)). The PAA manuscript number is
still not displayed; it is expected by e-mail.

    python tools/_p1342_record_paa_with_editor.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
AUTO = REPO / "AUTOMATION_HANDOVER.md"
FOLLOW = REPO / "docs" / "SUBMISSION_FOLLOWUP_2026-10-19.md"

SID = "0a4629f0-0a6d-45d8-b5b1-3681cc4adc8b"

ENT = """> **✅ 2026-10-19 15:25 —— A1 通过技术检查与编辑指派，状态变为 “With editor”（PAA 稿号仍待邮件）**
>
> 门户实测（操作者截图）：状态卡 **"You have an editor assessing your submission"**；进度条
> **Submission received ✓ → Technical check ✓ → Editorial assignment ✓ → With editor（当前）**。
>
> | 字段 | 值 |
> |---|---|
> | 期刊 | Pattern Analysis and Applications（Springer Nature Snapp）|
> | 当前状态 | **With editor**（编辑评估是否送审；可能直接要求修改或邀请审稿人）|
> | 已通过 | 技术检查（含声明/格式/查重）、编辑指派 |
> | Submission ID | `""" + SID + """` |
> | PAA 稿号 | **仍未显示 → 待邮件**（收到即回填 5 处文档 + 周提醒）|
>
> **下一步**：编辑可能 (a) 直接送审 → 出现 "Reviewer(s) invited"，(b) 要求修改 → 按 `docs/A1_REVIEWER_OBJECTIONS.md`
> 与 `docs/REVISION_CITATION_BACKLOG_2026-10-19.md` 起草修订，从**本地工作副本**（60 页，已含升级包 14 项）重建包，
> 冻结的投出版 PDF（58 页）与 `_frozen_submitted/` 保持不动。
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

    # HANDOFF entry
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "状态变为 “With editor”" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        changed += 1
        print("  handoff entry added")

    # which-paper row
    t = io.open(WHICH, encoding="utf-8").read()
    old = ("**2026-10-18 已投**（Submission received，Technical check in progress；Submission ID `" + SID + "`；"
           "PAA 稿号待邮件；包 `SUBMISSION/A1_PatternAnalysisApplications/`）")
    new = ("**2026-10-18 已投**（技术检查 ✓、编辑指派 ✓、**With editor**（2026-10-19）；Submission ID `" + SID + "`；"
           "PAA 稿号待邮件；包 `SUBMISSION/A1_PatternAnalysisApplications/`）")
    if old in t:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
        changed += 1
        print("  which-paper row updated")
    else:
        print("  which-paper row: pattern not found (left as is)")

    # file map status row + new entry
    m = io.open(MAP, encoding="utf-8").read()
    old2 = "**2026-10-18 已投 Pattern Analysis and Applications（SCIE）**：Submission received、Technical check in progress，"
    new2 = ("**2026-10-18 已投 Pattern Analysis and Applications（SCIE）**：技术检查 ✓、编辑指派 ✓、"
            "**With editor（2026-10-19）**，")
    if old2 in m:
        m = m.replace(old2, new2, 1)
        changed += 1
        print("  map status row updated")
    row = ("108. ✅ **A1 状态更新：With editor（2026-10-19 15:25）** —— 技术检查与编辑指派均通过，编辑正在评估是否送审；"
           "Submission ID `" + SID + "`；**PAA 稿号仍待邮件**。已同步 `HANDOFF`、`哪篇是哪篇`、`AUTOMATION`、"
           "`docs/SUBMISSION_FOLLOWUP_2026-10-19.md`。\n")
    if "A1 状态更新：With editor（2026-10-19 15:25）" not in m:
        anchor = "107. 🗺️ **P3/A23/Commentary 升级包方案"
        idx = m.find(anchor)
        assert idx >= 0, "map anchor missing"
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
        changed += 1
        print("  map row added")
    io.open(MAP, "w", encoding="utf-8", newline="").write(m)

    # automation handover heading
    a2 = io.open(AUTO, encoding="utf-8").read()
    old3 = "**2026-10-18 已投 Pattern Analysis and Applications（SCIE）**：Submission received、Technical check in progress，"
    new3 = ("**2026-10-18 已投 Pattern Analysis and Applications（SCIE）**：Technical check ✓、Editorial assignment ✓、"
            "**With editor（2026-10-19）**，")
    if old3 in a2:
        io.open(AUTO, "w", encoding="utf-8", newline="").write(a2.replace(old3, new3, 1))
        changed += 1
        print("  automation heading updated")

    # follow-up document: status row + a short history note
    f = io.open(FOLLOW, encoding="utf-8").read()
    old4 = ("| **A1** | Pattern Analysis and Applications（Snapp）| Submission ID `" + SID + "`；**PAA 稿号待邮件** | "
            "**Submission received ✓**；**Technical check in progress**；v.1.0；审稿文件 `latex_source.pdf` | "
            "等技术检查结果 / 编辑部下一步状态 |")
    new4 = ("| **A1** | Pattern Analysis and Applications（Snapp）| Submission ID `" + SID + "`；**PAA 稿号待邮件** | "
            "**With editor（2026-10-19）**：Submission received ✓、Technical check ✓、Editorial assignment ✓；v.1.0；"
            "审稿文件 `latex_source.pdf` | 等编辑决定：送审（Reviewer invited）或直接要求修改 |")
    if old4 in f:
        f = f.replace(old4, new4, 1)
        f = f.rstrip("\n") + ("\n\n## 五、状态历史\n\n"
                             "- **2026-10-18 19:5x**：投稿（提交 v1.0）；\n"
                             "- 2026-10-19 上午：Submission received → Technical check in progress；\n"
                             "- **2026-10-19 15:25**：Technical check ✓、Editorial assignment ✓ → **With editor**。\n")
        io.open(FOLLOW, "w", encoding="utf-8", newline="").write(f)
        changed += 1
        print("  follow-up status + history updated")
    else:
        print("  follow-up row: pattern not found (left as is)")

    print(f"  changed files: {changed}")
    return 0 if changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
