# -*- coding: utf-8 -*-
r"""Record the Neural Networks rejection of A1 (NEUNET-D-26-09426) everywhere it matters.

Desk rejection: the action editor returned the manuscript without external review, on the ground that "the technical
novelty on neural networks is marginal". Its predecessor NEUCOM-D-26-20952 had been desk-rejected by Neurocomputing on
2026-10-10, so the novelty framing is now the binding constraint on that paper.

Two consequences must land before Paper A is submitted today:
  * Paper A's cover letter disclosed this companion study as "under review at Neural Networks" -- no longer true;
  * A1's status is recorded as "under review" in several documents.

Status text only: no manuscript content changes, and the frozen submission copies are untouched. Line replacements are by
whole-line equality so no historical line is damaged silently.

    python tools/_p1197_record_a1_rejection.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

LETTER = """Decision letter, verbatim (received 2026-10-18)

Ms. Ref. No.: NEUNET-D-26-09426
Title: Order Preservation Tracks Zero-Shot Accuracy under Classification Fine-Tuning: Why the Modality Gap Is Not a
       Universal Health Metric
Mathematical and Computational Analysis
Neural Networks

Dear Mr Hongrui Wan,

Based on the action editor's recommendation and the enclosed referee reports, I regret to inform you that your
manuscript has been rejected. I nonetheless hope that you find the comments helpful.

To view your reviewer feedback, please log in as an author at https://www.editorialmanager.com/neunet/ and navigate to
your manuscript in the "Submissions with a Decision" folder under the Author Main Menu.

Thank you for submitting this article to Neural Networks, and I hope to receive your future submissions.

Yours sincerely,

Tongliang Liu, Co-Editor-in-Chief; The University of Sydney
Editorial Office
Neural Networks

Reviewers' comments:

AE: The technical novelty on neural networks is marginal. Therefore, I recommend that the submission be returned
without sending to reviewers, which also saves time for authors.

Note: no referee reports exist for this submission -- the action editor returned it without external review, so the
"enclosed referee reports" wording is boilerplate.
"""

COVER_OLD_RE = re.compile(
    r"\\item \\textbf\{A companion study on cross-modal alignment diagnostics\} under review at \\emph\{Neural\s*\n"
    r"Networks\}.*?overlap of results with the present manuscript\.",
    re.S,
)
COVER_NEW = (
    r"\item \textbf{A companion study on cross-modal alignment diagnostics} submitted to \emph{Neural" "\n"
    r"Networks} (``Order Preservation Tracks Zero-Shot Accuracy under Classification Fine-Tuning: Why the" "\n"
    r"Modality Gap Is Not a Universal Health Metric'', \texttt{NEUNET-D-26-09426}) and \emph{rejected at the" "\n"
    r"editorial stage without external review}. It shares the subject matter of modality-gap behaviour under" "\n"
    r"fine-tuning but asks a different question --- which of the two quantities, the gap or the rank-order" "\n"
    r"statistic $\tau$, tracks zero-shot accuracy --- and reports no overlap of results with the present" "\n"
    r"manuscript. Because it is unpublished, the present manuscript does not rely on it."
)

# whole-line replacements, keyed by an anchor that must occur exactly once in that file
LINES = {
    "文件地图.md": [
        ("| **A1** | `paper_a1/` | **42** | 在审 **Neural Networks NEUNET-D-26-09426**",
         "> | **A1** | `paper_a1/` | **42** | **2026-10-18 桌面拒稿（未送审，AE 判 novelty marginal）**；原在审 **Neural Networks NEUNET-D-26-09426**（2026-10-12）；0/0/0；56 文献 56/56；**本地工作副本已修**（提交件冻结未动） |"),
        ("| **A1** | 已转投 Neural Networks `NEUNET-D-26-09426`（2026-10-12）",
         "> | **A1** | **2026-10-18 桌面拒稿**（Neural Networks `NEUNET-D-26-09426`，2026-10-12 投） |"),
        ("本节已过期（2026-10-18 注）",
         "> ⚠️ **本节已过期（2026-10-18 注）**：A1 已于 **2026-10-12 投出 Neural Networks `NEUNET-D-26-09426`**，**2026-10-18 桌面拒稿（未送审）**；以顶部 2026-10-18 块为准。"),
        ("| 当前状态 | ~~ATS 转投待确认~~",
         "> | 当前状态 | ~~ATS 转投待确认~~ **2026-10-12 已投出 `NEUNET-D-26-09426` → 2026-10-18 桌面拒稿（未送审）** |"),
    ],
    "哪篇是哪篇.md": [
        ("**Neural Networks** ｜ **`NEUNET-D-26-09426`** ｜**在审**",
         "| `paper_a1/` | **A1** — Order Preservation / modality gap ≠ health metric | `main.tex` | **Neural Networks** ｜ **`NEUNET-D-26-09426`** ｜**桌面拒稿**（2026-10-18，未送审） | 42 |"),
        ("| `NEUNET-D-26-09426` | **Neural Networks** | **A1**（`paper_a1/`） |",
         "| `NEUNET-D-26-09426` | **Neural Networks** | **A1**（`paper_a1/`） | **桌面拒稿**（2026-10-18，AE 判 novelty 不足、未送审；2026-10-12 投；前身 `NEUCOM-D-26-20952` 于 2026-10-10 桌面拒稿） |"),
        ("1. **已投出/在审**：P3（PRL -02378R1）、A1（Neural Networks）",
         "1. **已投出/在审**：P3（PRL -02378R1）、A23（JOE）、PRL Commentary（PRL -02402）——**三篇冻结不动**；**A1 已于 2026-10-18 被 Neural Networks 桌面拒稿**（AE：novelty marginal，未送审），换刊方向待定。"),
    ],
    "AUTOMATION_HANDOVER.md": [
        ("**为什么重要**：P3（`PRLETTERS-D-26-02378R1`，R1 截止 2026-11-02）与 A1（转投确认期限 2026-11-08）都有硬期限",
         "**为什么重要**：P3（`PRLETTERS-D-26-02378R1`，R1 截止 2026-11-02）有硬期限；**A1 已于 2026-10-18 被 Neural Networks 桌面拒稿（novelty 不足、未送审），换刊待定**，竞争面变化需按周盯。"),
        ("### 3. A1（`paper_a1/`）｜`NEUNET-D-26-09426`（Neurocomputing ATS 转投邀请",
         "### 3. A1（`paper_a1/`）｜**2026-10-18 被 Neural Networks 桌面拒稿**（`NEUNET-D-26-09426`；前身 `NEUCOM-D-26-20952` 亦桌面拒；新刊待定）"),
        ("- **A1 / A23 / PRL Commentary**：均在审、冻结不动",
         "- **A23 / PRL Commentary**：均在审、冻结不动；**A1 已于 2026-10-18 被 Neural Networks 桌面拒稿**（本地工作副本的 Data availability/日期修复保留，供改投）；修回时按 `docs/AUDIT_2026-10-18_five_manuscripts.md` §3–§5 处理。"),
    ],
    "paper_a1/README_是哪篇.md": [
        ("| **当前状态** | **在审**（2026-10-12 投出",
         "| **当前状态** | **桌面拒稿（2026-10-18）**：AE 判 \"technical novelty on neural networks is marginal\"、**未送外审**；2026-10-12 投出；前身 `NEUCOM-D-26-20952` 于 2026-10-10 桌面拒稿 |"),
    ],
    "docs/AUDIT_2026-10-18_five_manuscripts.md": [
        ("## 3. A1（`paper_a1/`）—— Neural Networks `NEUNET-D-26-09426` 在审",
         "## 3. A1（`paper_a1/`）—— Neural Networks `NEUNET-D-26-09426` **桌面拒稿（2026-10-18）**"),
    ],
}

HANDOFF_ENT = """> **❌ 2026-10-18 12:15 —— A1 被 Neural Networks 桌面拒稿（`NEUNET-D-26-09426`，8 天内第二次桌面拒）**
>
> 编辑部来函（`Tongliang Liu, Co-Editor-in-Chief`）通知**拒稿**；**AE 明确说明未送外审**：
> > "The technical novelty on neural networks is marginal. Therefore, I recommend that the submission be returned
> > without sending to reviewers, which also saves time for authors."
>
> 原件存档：`docs/reviews/A1_NEUNET-D-26-09426_reject_2026-10-18.txt`（信中"enclosed referee reports"为模板话术，**无外审意见**）。
>
> | 事实 | 值 |
> |---|---|
> | 稿号 | `NEUNET-D-26-09426`（Neural Networks，Section: Mathematical and Computational Analysis）|
> | 投出 → 决定 | 2026-10-12 → **2026-10-18**（6 天）|
> | 类型 | **桌面拒稿**（无外审）|
> | 前身 | `NEUCOM-D-26-20952`，**2026-10-10** 被 Neurocomputing 桌面拒稿（ATS 转投 NN）|
> | ⇒ 判断 | **8 天内两次桌面拒、均在"新颖性"上** —— A1 当前框架撞的是新颖性门槛，不是格式或数据问题 |
>
> ### 一、连带修改（今日必须做，因 Paper A 今天投）
>
> | 位置 | 改动 |
> |---|---|
> | **Paper A 揭示函**（`cover_letter_nc.tex` + `cover_letter.tex`）| 第 3 项由"companion study **under review** at Neural Networks" ⇒ "**rejected at the editorial stage without external review**"，并加"因其未发表，本文不依赖其结论"；已重编译并刷新投稿包 |
> | `文件地图.md`、`哪篇是哪篇.md`、`docs/AUDIT_2026-10-18_five_manuscripts.md`、`AUTOMATION_HANDOVER.md`、`paper_a1/README_是哪篇.md` | A1 状态 `在审` → `2026-10-18 桌面拒稿`（**整行替换，历史条目保留**）|
>
> ### 二、A1 本地工作副本不受影响
>
> 昨夜（00:50）为"修回"补的 Data availability / 日期统一（`paper_a1/FIXES_2026-10-18.md`）**仍有效，可直接用于改投**；
> 已投出冻结件 `SUBMISSION/A1_NeuralNetworks/` **未动**。
>
> ### 三、A1 下一步（三条路，待操作者定，未擅自行动）
>
> 1. **换刊**：回避"神经网络新颖性"标尺，投偏实证/应用的刊（Image and Vision Computing / Pattern Analysis and
>    Applications / Computer Vision and Image Understanding 一类）——PR、Neurocomputing、Neural Networks 三条线已用尽；
> 2. **提新颖性再投**：把 order-preservation 与 Paper A 的 ODE 理论合并，但这会与 Paper A 实质重叠，
>    **须等 Paper A 审稿结论**，否则构成重复投稿风险；
> 3. **挂 arXiv 保优先权**，暂不再投期刊。
>
> ⚠️ 与 Paper A 的关系：**不同问题、无结果重叠**（A1 问"gap 是否通用健康指标"，Paper A 问"适配位置如何影响 gap"），
> 故 Paper A **今日照常投 Neurocomputing**；揭示函已按拒稿事实改写。
>
"""


def find_line(lines, anchor):
    hits = [i for i, l in enumerate(lines) if anchor in l]
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("  [0] archive letter ->", "docs/reviews/A1_NEUNET-D-26-09426_reject_2026-10-18.txt")

    print("  [1] Paper A cover letters")
    covers = {}
    for name in ("cover_letter_nc.tex", "cover_letter.tex"):
        p = REPO / "paper合" / name
        t = io.open(p, encoding="utf-8").read()
        assert COVER_OLD_RE.search(t), name
        covers[p] = COVER_OLD_RE.sub(lambda _m: COVER_NEW, t, count=1)
        print(f"    {name}: disclosure item rewritten")

    print("  [2] status documents (whole-line replacements)")
    staged = {}
    for rel, pairs in LINES.items():
        p = REPO / rel
        lines = io.open(p, encoding="utf-8").read().split("\n")
        for anchor, new_line in pairs:
            hits = find_line(lines, anchor)
            print(f"    {rel:<44} anchor {anchor[:30]!r}: {len(hits)}")
            assert len(hits) == 1, f"{rel}: anchor {anchor!r} matched {len(hits)} lines"
            lines[hits[0]] = new_line
        staged[p] = "\n".join(lines)

    if not a.apply:
        print("\n  (dry run)")
        return 0

    out = REPO / "docs" / "reviews" / "A1_NEUNET-D-26-09426_reject_2026-10-18.txt"
    out.write_text(LETTER, encoding="utf-8")
    print("  wrote", out.relative_to(REPO))
    for p, t in covers.items():
        io.open(p, "w", encoding="utf-8", newline="").write(t)
        print("  cover letter updated:", p.name)
    for p, t in staged.items():
        io.open(p, "w", encoding="utf-8", newline="").write(t)
        print("  updated:", p.relative_to(REPO))
    h = io.open(REPO / "HANDOFF.md", encoding="utf-8").read()
    if "A1 被 Neural Networks 桌面拒稿" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(REPO / "HANDOFF.md", "w", encoding="utf-8", newline="").write(
            h[: j + 1] + "\n" + HANDOFF_ENT + h[j + 1:])
        print("  handoff entry added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
