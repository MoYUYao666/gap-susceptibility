# -*- coding: utf-8 -*-
r"""Record the Neurocomputing status change for Paper A: With Editor (status changed 2026-10-19 12:08 AM).

Evidence: the operator pasted the Editorial Manager row:
  NEUCOM-D-26-23760  Adaptation Site and the Modality Gap: ...  Oct 18 2026 9:19AM  Oct 19 2026 12:08AM  With Editor

    python tools/_p1350_record_neucom_with_editor.py [--apply]
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

ENT = """> **✅ 2026-10-19 18:40 —— Paper A（Neurocomputing `NEUCOM-D-26-23760`）进入 “With Editor”**
>
> EM 实测行：`NEUCOM-D-26-23760  Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow
> Theory for PEFT of Contrastive Dual-Encoders  |  Submitted Oct 18 2026 9:19AM  |  status changed Oct 19 2026 12:08AM
> |  **With Editor**`。
>
> | 字段 | 值 |
> |---|---|
> | 稿件 | Paper A（`paper合/`）|
> | 期刊 / 平台 | Neurocomputing / Elsevier Editorial Manager |
> | 稿号 | **`NEUCOM-D-26-23760`** |
> | 提交时间 | Oct 18 2026 9:19 AM（EM 显示）|
> | 状态变更 | Oct 19 2026 12:08 AM → **With Editor** |
> | 当前阶段 | 编辑评估是否送审（对应 Snapp 流程的 "With editor"；可能直接要求修改或邀请审稿人）|
>
> **下一步**：等 EM 状态变为 "Under Review" / 收到审稿意见；若要求修改，从**本地工作副本**（NC 72 页 / Springer 52 页，
> 已含升级包与补引）重建包，冻结的投出版 PDF（70 页）与 `_frozen_submitted/` 保持不动。
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
    if "Paper A（Neurocomputing `NEUCOM-D-26-23760`）进入 “With Editor”" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        changed += 1
        print("  handoff entry added")

    w = io.open(WHICH, encoding="utf-8").read()
    old = "**2026-10-18 已投出，状态 Submitted**，稿号 **`NEUCOM-D-26-23760`**（包 `SUBMISSION/PaperA_Neurocomputing/`）"
    new = ("**2026-10-18 已投出**，状态 **With Editor**（2026-10-19 12:08），稿号 **`NEUCOM-D-26-23760`**"
           "（包 `SUBMISSION/PaperA_Neurocomputing/`）")
    if old in w:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
        changed += 1
        print("  which-paper row updated")
    else:
        print("  which-paper row: pattern not found")

    m = io.open(MAP, encoding="utf-8").read()
    old2 = "**2026-10-18 投 Neurocomputing（稿号 `NEUCOM-D-26-23760`）**；"
    new2 = "**2026-10-18 投 Neurocomputing（稿号 `NEUCOM-D-26-23760`）→ With Editor（2026-10-19 12:08）**；"
    if old2 in m:
        m = m.replace(old2, new2, 1)
        changed += 1
        print("  map status row updated")
    row = ("111. ✅ **Paper A 进入 With Editor（2026-10-19 18:40）** —— Neurocomputing `NEUCOM-D-26-23760`：Submitted "
           "Oct 18 9:19AM，状态变更 Oct 19 12:08AM，**With Editor**；已同步 `HANDOFF`、`哪篇是哪篇`、`AUTOMATION`、"
           "`docs/SUBMISSION_FOLLOWUP_2026-10-19.md`；冻结的 70 页投出版不动。\n")
    if "Paper A 进入 With Editor（2026-10-19 18:40）" not in m:
        anchor = "110. ✅ **三稿复审 READY/A"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
        changed += 1
        print("  map row added")
    io.open(MAP, "w", encoding="utf-8", newline="").write(m)

    a2 = io.open(AUTO, encoding="utf-8").read()
    old3 = "### 1. Paper A（`paper合/`）｜**2026-10-18 已投 Neurocomputing**（门户状态 Submitted；稿号 `NEUCOM-D-26-23760`）"
    new3 = ("### 1. Paper A（`paper合/`）｜**2026-10-18 已投 Neurocomputing**（`NEUCOM-D-26-23760`；"
            "**2026-10-19 12:08 状态 With Editor**）")
    if old3 in a2:
        a2 = a2.replace(old3, new3, 1)
        a2 = a2.replace("- **Paper A**：2026-10-18 已投 Neurocomputing，门户状态 **Submitted**；**稿号待补**（确认邮件/EM 取）。",
                        "- **Paper A**：2026-10-18 已投 Neurocomputing（`NEUCOM-D-26-23760`），"
                        "**2026-10-19 进入 With Editor**。")
        io.open(AUTO, "w", encoding="utf-8", newline="").write(a2)
        changed += 1
        print("  automation updated")

    f = io.open(FOLLOW, encoding="utf-8").read()
    old4 = "| **Paper A** | Neurocomputing（Elsevier EM）| **`NEUCOM-D-26-23760`** | **Submitted**（2026-10-18）| 等 EM 状态变为 \"With Editor\" |"
    new4 = ("| **Paper A** | Neurocomputing（Elsevier EM）| **`NEUCOM-D-26-23760`** | **With Editor**（状态变更 "
            "2026-10-19 12:08；提交 2026-10-18 9:19）| 等送审 → 出现 Under Review / 收到审稿意见 |")
    if old4 in f:
        f = f.replace(old4, new4, 1)
        f = f.rstrip("\n") + ("\n\n- **2026-10-19 12:08（EM）**：Paper A 状态 **With Editor**。\n")
        io.open(FOLLOW, "w", encoding="utf-8", newline="").write(f)
        changed += 1
        print("  follow-up updated")
    print(f"  changed files: {changed}")
    return 0 if changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
