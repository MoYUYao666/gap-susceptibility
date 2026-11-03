# -*- coding: utf-8 -*-
r"""Update the A1 cover letter (Paper A is now submitted) and refresh AUTOMATION_HANDOVER.md.

The cover letter said the companion manuscript "is being handled separately"; Paper A was submitted to Neurocomputing
on 2026-10-18, so the letter now states that. The automation handover still described Paper A as unsubmitted and A1 as
having no venue, and its verbatim prompt text carries the same stale facts.

    python tools/_p1269_fix_coverletter_automation.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL = os.path.join(REPO, "paper_a1", "cover_letter_paa.tex")
AUTO = os.path.join(REPO, "AUTOMATION_HANDOVER.md")

CL_OLD = ("A companion manuscript on adaptation-site dynamics is\nbeing handled separately. Neither reports the results of this manuscript;")
CL_NEW = ("A companion manuscript on adaptation-site dynamics is under consideration at \\emph{Neurocomputing} "
          "(submitted October 2026). Neither reports the results of this manuscript;")

AUTO_PAIRS = [
    ("### 1. Paper A（`paper合/`）｜目标 Neurocomputing（未投，无稿号）",
     "### 1. Paper A（`paper合/`）｜**2026-10-18 已投 Neurocomputing**（门户状态 Submitted；稿号待补）"),
    ("### 3. A1（`paper_a1/`）｜**2026-10-18 被 Neural Networks 桌面拒稿**（`NEUNET-D-26-09426`；前身 `NEUCOM-D-26-20952` 亦桌面拒；新刊待定）",
     "### 3. A1（`paper_a1/`）｜**2026-10-18 被 Neural Networks 桌面拒稿**（`NEUNET-D-26-09426`；前身 `NEUCOM-D-26-20952` 亦桌面拒）"
     "→ **已定型改投 Pattern Analysis and Applications（SCIE），包就绪（51 页），待投**"),
    ("｜目标 Neurocomputing（未投，无稿号）", "｜已投 Neurocomputing（2026-10-18，状态 Submitted，稿号待补）"),
    ("新刊待定", "已改投 Pattern Analysis and Applications（SCIE），待投"),
    ("A1 转投确认 2026-11-08", "A1 的 PAA 投稿（无 deadline）"),
]

STATUS = """
## 状态更新（2026-10-18 18:40）

- **Paper A**：2026-10-18 已投 Neurocomputing，门户状态 **Submitted**；**稿号待补**（确认邮件/EM 取）。
- **A1**：Neural Networks 桌面拒稿后，已定型改投 **Pattern Analysis and Applications**（SCIE）；
  包在 `SUBMISSION/A1_PatternAnalysisApplications/`（**51 页** + 1 页 title page + 揭示函），审计 `a1_paa` READY/A，**待投**。
- **P3**：`PRLETTERS-D-26-02378R1` 在审（2 位审稿人，1 份意见完成）；**在审期间不接受替换件**，勘误留修订轮；R1 截止 2026-11-02。
- **A23**：IEEE JOE `26-0663` 在审。**PRL Commentary**：`PRLETTERS-D-26-02402` 在审。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    cl = io.open(CL, encoding="utf-8").read()
    n = cl.count(CL_OLD)
    print(f"  cover-letter companion sentence: {n}")
    assert n == 1
    cl = cl.replace(CL_OLD, CL_NEW, 1)

    au = io.open(AUTO, encoding="utf-8").read()
    for old, new in AUTO_PAIRS:
        c = au.count(old)
        print(f"  automation {old[:44]!r}: {c}")
        if c:
            au = au.replace(old, new)
    if "## 状态更新（2026-10-18 18:40）" not in au:
        anchor = "## 五、当前状态（交接时点 2026-10-17 21:20）"
        i = au.find(anchor)
        assert i > 0
        au = au[:i] + STATUS.strip() + "\n\n" + au[i:]
        print("  automation status block added")

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(CL, "w", encoding="utf-8", newline="").write(cl)
    io.open(AUTO, "w", encoding="utf-8", newline="").write(au)
    print("  written cover letter and automation handover")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
