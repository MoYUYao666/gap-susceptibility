# -*- coding: utf-8 -*-
r"""Record the PRL editorial reply about P3's replacement files.

The Editor declined to accept corrected files while the manuscript is under review (two reviewers assigned, one report
complete, one in progress) and said corrections can be addressed if a revision is requested. That means the locally
repaired "abla"/overfull version cannot be adopted now: the under-review PDF keeps the defect, and the corrected build in
`SUBMISSION/P3_PRL_revision/CORRECTED_2026-10-15/` becomes the basis for the revision round.

    python tools/_p1250_record_p3_editor_reply.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LETTER = REPO / "docs" / "reviews" / "P3_PRLETTERS-D-26-02378R1_EM_reply_2026-10-18.txt"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
P3DOC = REPO / "docs" / "P3_AUDIT_10PP_2026-10-17.md"

EMAIL = """PRL editorial reply on replacement files for P3 (received 2026-10-18; verbatim, signature block trimmed)

Subject: manuscript PRLETTERS-D-26-02378R1 - "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry"

Dear Dr. Wan,

Thank you for your patience while I sought clarification from the handling Editor regarding your request to submit
corrected files for manuscript PRLETTERS-D-26-02378R1, entitled "Zero-Shot Cross-Architecture Rank Allocation from
Gradient Geometry."

I have now received a response from the Editor. The manuscript has already been assigned to two reviewers, with one
review completed and the second review currently in progress. Given that the peer review process is underway, the Editor
has advised that it would be best to keep the submitted manuscript and supplementary materials unchanged until the
current round of review has been completed.

At this time, replacement files cannot be accommodated during the ongoing review process. Should any revisions be
requested following the completion of this review round, there may be an opportunity to address the corrections at that
stage.

I understand your concern regarding the identified errors and appreciate your proactive effort to bring them to our
attention.

Thank you for your understanding and patience.

Kind regards,

[Editorial Office, Pattern Recognition Letters]

Recorded consequences for this repository:
  * the submitted PDFs under SUBMISSION/P3_PRL_revision/{CORRECTED_2026-10-15,UPLOAD_2026-10-15} must not be replaced;
  * the locally repaired build (nabla fixes, overfull fixes, dead labels) stays staged for the revision round;
  * the under-review PDF still prints "abla" (one occurrence) until that revision;
  * review status: two reviewers assigned, one report complete, one in progress.
"""

ENT = """> **📨 2026-10-18 17:05 —— PRL 编辑部回信：**P3 在审期间不接受替换件**；勘误留到修订轮**
>
> 编辑部（Pattern Recognition Letters，关于 `PRLETTERS-D-26-02378R1`）明确：
> - 稿件**已分配 2 位审稿人：1 份意见完成、1 份进行中**；
> - 编辑建议**在审期间保持稿件与补充材料不变**；
> - **"At this time, replacement files cannot be accommodated during the ongoing review process"**；
> - 若本轮后收到修订要求，**可在修订阶段处理这些更正**。
>
> **对我们的含义**：
> 1. 本地已修好的 `abla`/Overfull/死标签版本**本次无法采纳**；在审 PDF 仍印 1 处 "abla"，**留待修订轮**；
> 2. `SUBMISSION/P3_PRL_revision/CORRECTED_2026-10-15/` 与 `UPLOAD_2026-10-15/` 的**冻结件保持原样**（哈希未变），
>    本地修复版本继续作为**修订素材**；
> 3. 收到 revision 决定时：以本地修正版为基础重建，并附逐条 response；
> 4. 邮件已存档 `docs/reviews/P3_PRLETTERS-D-26-02378R1_EM_reply_2026-10-18.txt`。
>
> **下一步**：等审稿结果（无需操作）；R1 修订截止仍按 **2026-11-02** 关注。
>

"""

WHICH_DIR_OLD = ("**Under Review**（2026-10-13 投 R1；替换件 2026-10-15 已发）")
WHICH_DIR_NEW = ("**Under Review**（R1 2026-10-13 投；**2 审稿人：1 完成 1 进行中**；"
                 "2026-10-18 编辑部回信：**在审期间不接受替换件**）")
WHICH_TAB_OLD = "**Under Review**（R1 于 2026-10-13 投；2026-10-15 替换件申请已发）"
WHICH_TAB_NEW = ("**Under Review**（R1 2026-10-13 投；2 审稿人：1 完成 1 进行中；"
                 "**替换件请求被拒**，勘误留修订轮）")

MAP_OLD = '本地源已修 \\nabla/Overfull（提交件哈希未变，仍印 "abla"，下轮修）'
MAP_NEW = ('本地源已修 \\nabla/Overfull（提交件哈希未变，仍印 "abla"，下轮修）；'
           '**2026-10-18 编辑部回信：在审期间不接受替换件**（2 审稿人，1 完成 1 进行中）')

P3DOC_APPEND = """

## 编辑部回复：在审期间不接受替换件（2026-10-18）

Pattern Recognition Letters 编辑部回信（全文存 `docs/reviews/P3_PRLETTERS-D-26-02378R1_EM_reply_2026-10-18.txt`）：
稿件已分配 **2 位审稿人（1 份意见完成、1 份进行中）**，编辑建议在审期间保持稿件与补充材料不变；
**"replacement files cannot be accommodated during the ongoing review process"**，更正可在修订阶段处理。

因此：本节所述的本地修复（nabla、Overfull、死标签）**不用于当前在审版本**；在审 PDF 仍印 1 处 `abla`。
`CORRECTED_2026-10-15/` 与 `UPLOAD_2026-10-15/` 保持冻结，作为修订轮的基础。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    LETTER.write_text(EMAIL, encoding="utf-8")
    print("  letter archived:", LETTER.relative_to(REPO))

    h = io.open(HANDOFF, encoding="utf-8").read()
    if "PRL 编辑部回信：**P3 在审期间不接受替换件**" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")

    w = io.open(WHICH, encoding="utf-8").read()
    for old, new, label in ((WHICH_DIR_OLD, WHICH_DIR_NEW, "P3 dir row"), (WHICH_TAB_OLD, WHICH_TAB_NEW, "P3 status row")):
        n = w.count(old)
        print(f"  {label}: {n}")
        if n == 1:
            w = w.replace(old, new, 1)
    io.open(WHICH, "w", encoding="utf-8", newline="").write(w)

    m = io.open(MAP, encoding="utf-8").read()
    n = m.count(MAP_OLD)
    print(f"  map P3 line: {n}")
    if n == 1:
        m = m.replace(MAP_OLD, MAP_NEW, 1)
    io.open(MAP, "w", encoding="utf-8", newline="").write(m)

    p = io.open(P3DOC, encoding="utf-8").read()
    if "在审期间不接受替换件" not in p:
        io.open(P3DOC, "w", encoding="utf-8", newline="").write(p.rstrip("\n") + P3DOC_APPEND)
        print("  P3 audit doc appended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
