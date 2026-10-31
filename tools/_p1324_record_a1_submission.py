# -*- coding: utf-8 -*-
r"""Record the A1 submission to Pattern Analysis and Applications (Springer Nature portal).

Facts (2026-10-18, read from the portal page after submission):
  * journal            Pattern Analysis and Applications
  * article type       Research
  * submission ID      0a4629f0-0a6d-45d8-b5b1-3681cc4adc8b  (SNAPP internal id; the PAA manuscript number arrives by email)
  * status             Submission received (done) -> Technical check (in progress)
  * version            v.1.0
  * reviewed file      latex_source.pdf, compiled by the portal from latex_source.zip (58 pages, verified identical to our PDF)

    python tools/_p1324_record_a1_submission.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SID = "0a4629f0-0a6d-45d8-b5b1-3681cc4adc8b"
NUM_A = "NEUCOM-D-26-23760"

EDITS = {
    "哪篇是哪篇.md": [
        ("**Pattern Analysis and Applications**（SCIE）｜**待投**（包就绪：`SUBMISSION/A1_PatternAnalysisApplications/`）",
         "**Pattern Analysis and Applications**（SCIE）｜**2026-10-18 已投**（Submission received，Technical check in progress；"
         "Submission ID `" + SID + "`；PAA 稿号待邮件；包 `SUBMISSION/A1_PatternAnalysisApplications/`）"),
    ],
    "AUTOMATION_HANDOVER.md": [
        ("→ **已定型改投 Pattern Analysis and Applications（SCIE），包就绪（51 页），待投**",
         "→ **2026-10-18 已投 Pattern Analysis and Applications（SCIE）**：Submission received、Technical check in progress，"
         "Submission ID `" + SID + "`；PAA 稿号待邮件（包 `SUBMISSION/A1_PatternAnalysisApplications/`，58 页）"),
        ("- **A1**：Neural Networks 桌面拒稿后，已定型改投 **Pattern Analysis and Applications**（SCIE）；",
         "- **A1**：Neural Networks 桌面拒稿后已投 **Pattern Analysis and Applications**（SCIE，2026-10-18）；"),
    ],
    "SUBMISSION/A1_PatternAnalysisApplications/README.md": [
        ("Compliance (Pattern Analysis and Applications guide, read 2026-10-18): abstract 249 words",
         "| Submission status | **Submitted 2026-10-18** to the Springer Nature portal (Submission ID `" + SID + "`); "
         "Submission received, technical check in progress; PAA manuscript number pending by email |\n"
         "Compliance (Pattern Analysis and Applications guide, read 2026-10-18): abstract 249 words"),
    ],
    "文件地图.md": [
        ("> | **A1** | `paper_a1/` | **42** | **2026-10-18 桌面拒稿（未送审，AE 判 novelty marginal）**；原在审 **Neural Networks NEUNET-D-26-09426**（2026-10-12）；0/0/0；56 文献 56/56；**本地工作副本已修**（提交件冻结未动） |",
         "> | **A1** | `paper_a1/` | **58** | **2026-10-18 已投 Pattern Analysis and Applications（SCIE）**：Submission received、"
         "Technical check in progress，Submission ID `" + SID + "`；此前 Neural Networks `NEUNET-D-26-09426` 桌面拒（2026-10-12）；"
         "0/0/0；台账 **157/157**；审计 READY/A |"),
    ],
}

HANDOFF_ENTRY = """> **📨 2026-10-18 22:00 —— A1 已投 Pattern Analysis and Applications（Submission received；Technical check in progress）**
>
> 两封投稿均已落地：
>
> | 稿件 | 期刊 | 状态（2026-10-18）| 编号 |
> |---|---|---|---|
> | **Paper A**（`paper合/`）| Neurocomputing | **Submitted** | **`""" + NUM_A + """`** |
> | **A1**（`paper_a1/`）| Pattern Analysis and Applications | **Submission received → Technical check in progress** | Submission ID `""" + SID + """`（PAA 稿号待邮件）|
>
> A1 投递事实（Springer Nature 门户实测）：Article type **Research**；版本 **v.1.0**；审稿文件 `latex_source.pdf`（门户由
> `latex_source.zip` 编译，**58 页**，与本地 PDF 首页逐字一致、无 Type 3 字体）；Cover Letter 已上传；Declarations 全填
> （competing interests none / dual publication no / third-party no / data availability Zenodo DOI / funding none）；
> 预印本选择 **No**；页面 3 条 hyperref 书签警告为无害项（不影响正文）。
>
> **剩余待补**：PAA 稿号（技术检查通过后邮件给出）；公开镜像待推送（见下条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for rel, pairs in EDITS.items():
        p = REPO / rel
        t = io.open(p, encoding="utf-8").read()
        for old, new in pairs:
            n = t.count(old)
            print(f"  {rel}: {n} x {old[:44]!r}")
            if n:
                t = t.replace(old, new, 1)
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(t)
    h = io.open(REPO / "HANDOFF.md", encoding="utf-8").read()
    need = "A1 已投 Pattern Analysis and Applications（Submission received" not in h
    print(f"  handoff entry needed: {need}")
    if a.apply and need:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(REPO / "HANDOFF.md", "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + HANDOFF_ENTRY + h[j + 1:])
        print("  handoff entry added")
    m = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("98. 📨 **A1 投稿落地（2026-10-18 22:00）** —— 投 **Pattern Analysis and Applications**（Springer Nature 门户）："
           "Submission received、Technical check in progress；Submission ID `" + SID + "`；Research 类型、v1.0、审稿 PDF "
           "**58 页**（门户编译，与本地一致）；PAA 稿号待邮件。Paper A 稿号 **`" + NUM_A + "`**。\n")
    if "A1 投稿落地" not in m:
        anchor = "97. 🔢 **Paper A 稿号回填"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        if a.apply:
            io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
