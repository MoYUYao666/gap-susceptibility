# -*- coding: utf-8 -*-
r"""Correct the submission-status records: Paper A is prepared, not confirmed submitted; A1 now targets PAA.

`哪篇是哪篇.md` said Paper A was "2026-10-18 投出". No manuscript number exists anywhere in the repository, and the line
came from the five-manuscript audit commit that recorded the operator's plan as a fact. Under the repository's own rule
(submission facts are only recorded with evidence; missing fields are marked 待核), the line is corrected, and the status
snapshot is written to HANDOFF and the map.

    python tools/_p1246_fix_submission_status.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WHICH = REPO / "哪篇是哪篇.md"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

OLD_PA = ("| `paper合/` | **Paper A = P1+P2** ⭐ 当前主稿 | `main_nc.tex` | **Neurocomputing**（elsarticle）｜"
          "**2026-10-18 投出**｜包 `NC_submission/` 已就绪 | **NC 70**｜Springer 50 |")
NEW_PA = ("| `paper合/` | **Paper A = P1+P2** ⭐ 当前主稿 | `main_nc.tex` | **Neurocomputing**（elsarticle）｜"
          "**待投**（包就绪：`SUBMISSION/PaperA_Neurocomputing/`；**稿号待补**）| **NC 70**｜Springer 50 |")

OLD_A1 = ("| `paper_a1/` | **A1** — Order Preservation / modality gap ≠ health metric | `main.tex` | "
          "**Neural Networks** ｜ **`NEUNET-D-26-09426`** ｜**桌面拒稿**（2026-10-18，未送审） | 42 |")
NEW_A1 = ("| `paper_a1/` | **A1** — Order Preservation / modality gap ≠ health metric | `main.tex` | "
          "**Pattern Analysis and Applications**（SCIE）｜**待投**（包就绪：`SUBMISSION/A1_PatternAnalysisApplications/`）；"
          "前投 Neural Networks `NEUNET-D-26-09426` **2026-10-18 桌面拒稿**（未送审） | 45 + 1 title page |")

NOTE = """
> ⚠️ **2026-10-18 16:05 更正**：本表此前把 Paper A 记为"2026-10-18 投出"，但**仓库内不存在任何稿号证据**
> （`73267d9` 的五稿复核把计划写成了事实）。按"投递类事实只写有证据的、缺字段记待核"的规则，现改为**待投（稿号待补）**。
> 若操作者已实际投出，请把稿号补到本行与 `HANDOFF.md`。
"""

ENT = """> **📊 2026-10-18 16:05 —— 投稿状态快照（逐条按仓库证据核过；并更正一处"把计划写成事实"的记录）**
>
> | 稿件 | 期刊 | 稿号 | 状态 |
> |---|---|---|---|
> | **P3** | Pattern Recognition Letters | `PRLETTERS-D-26-02378R1` | 🔄 **在审**：R1 于 2026-10-13 投出，替换件 2026-10-15 已发；**截止 2026-11-02** |
> | **A23** | IEEE J. Oceanic Engineering | `26-0663` | 🔄 **在审**（系统时间 2026-09-21）|
> | **PRL Commentary** | Pattern Recognition Letters | `PRLETTERS-D-26-02402` | 🔄 **在审**（2026-09-28 投）|
> | **Paper A** | Neurocomputing | **无** | ⏳ **待投**：包已就绪 `SUBMISSION/PaperA_Neurocomputing/`（70 页，审计 READY/A）；**稿号待补** |
> | **A1** | Pattern Analysis and Applications | **无** | ⏳ **待投**：包就绪 `SUBMISSION/A1_PatternAnalysisApplications/`（45 页 + title page，审计 READY/A）；前投 NN 已于 2026-10-18 桌面拒 |
> | **P1** | Pattern Recognition | `PR-D-26-10149` | ❌ 已拒（2026-10-12），内容并入 Paper A |
> | **P2** | — | — | 已并入 Paper A，无独立投稿 |
> | **ap3** | — | — | 归档，未投（含 P3 内容，不可投）|
> | **paper_review** | — | — | 综述素材，未投 |
>
> **更正**：`哪篇是哪篇.md` 原写 Paper A "2026-10-18 投出" —— 仓库无任何稿号证据（该结论来自 `73267d9` 把计划记成事实），
> 已改为**待投（稿号待补）**。若确已投出，请补稿号，我会立即回填并更新每周检索的状态文本。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    w = io.open(WHICH, encoding="utf-8").read()
    for old, new, label in ((OLD_PA, NEW_PA, "Paper A row"), (OLD_A1, NEW_A1, "A1 row")):
        n = w.count(old)
        print(f"  {label}: occurrences {n}")
        assert n == 1, label
        w = w.replace(old, new, 1)
    if "2026-10-18 16:05 更正" not in w:
        i = w.find("## 一、根目录的 8 个 `paper*`")
        assert i > 0
        w = w[:i] + NOTE.strip() + "\n\n" + w[i:]
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(WHICH, "w", encoding="utf-8", newline="").write(w)
    print("  corrected 哪篇是哪篇.md")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "投稿状态快照（逐条按仓库证据核过" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff snapshot added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("79. 📊 **投稿状态快照 + 更正一处把计划写成事实的记录（2026-10-18 16:05）** —— 在审：P3（R1，截止 11-02）、"
           "A23（09-21）、Commentary（09-28）；**待投**：Paper A（包就绪、稿号待补）、A1（PAA 包就绪）；已拒：P1、A1 的前投；"
           "P2 并入 Paper A；ap3/paper_review 未投。**更正**：`哪篇是哪篇.md` 原写 Paper A「2026-10-18 投出」但仓库无稿号证据 → 改为待投。\n")
    if "投稿状态快照 + 更正" not in m:
        anchor = "78. 🗂️ **`SUBMISSION/` 整理完成"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
