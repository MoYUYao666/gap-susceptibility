# -*- coding: utf-8 -*-
"""Record the A1 / Paper A package refresh round in the hand-off documents."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

entry = """> **🔧 2026-10-24 14:05 —— 修完 A1 / Paper A 投稿包陈旧问题；六稿审计全部 READY (A)**
>
> - **问题**：`paper_audit` 报 `A1 BLOCKED(D)`、`PaperA_nc BLOCKED(D)`，唯一 FAIL 是 **I-02 包内副本与当前主稿不一致**（A1：Manuscript.pdf 为 58 页旧版 vs 主稿 64 页；Paper A：Manuscript/Cover Letter/Highlights 均为 10-17 旧版 vs 主稿 74 页），另有 I-06 包 README 页数/摘要词数过期；
> - **修复**（`tools/_p1576_refresh_a1_papera_packages.py --apply`，幂等带断言）：
>   1. 旧包整体归档到 `SUBMISSION/_archive/A1_PAA_package_2026-10-18/`（33 文件）与 `SUBMISSION/_archive/PaperA_NEUCOM_package_2026-10-18/`（54 文件）；投出件仍在 `SUBMISSION/_frozen_submitted/`（未动）；
>   2. 按 profile 的 `package_map` 刷新：A1 `Manuscript.pdf` ← `paper_a1/main.pdf`；Paper A `Manuscript.pdf` ← `main_nc.pdf`、`Cover Letter.pdf` ← `cover_letter_nc.pdf`、`Highlights.pdf` ← `highlights_nc.pdf`（哈希断言一致）；
>   3. `latex_source.zip` 按**原有包含清单**用当前源码重建，并同步 `latex_source/` 目录树（A1 21 条目、Paper A 45 条目，条目数=树文件数）；
>   4. README 实测事实改为 **A1 64 页 / 249 词**、**Paper A 74 页 / 242 词**，并更新投稿状态行（A1 已 With editor 2026-10-19；Paper A 稿号 `NEUCOM-D-26-23760`）；
> - **复核**：六 profile 全部 **READY grade A、0 fail / 0 warn**（A1 61 PASS、Paper A nc 67 PASS）；provenance **PASS**；台账 **96/96**；`final_verification` **ALL PASS**；页数实测 A1 64 / Paper A NC 74 / Springer 53 / P3 10 / A23 70 / Commentary 7；
> - **仍未做（等决定）**：五篇全部在等编辑决定；`SUBMISSION/_venue_builds/*_next` 已是当前源码的下一次投稿包；P3 若修回需把 Data statement 的 DOI 从 v2.2 更新为 v2.3（`10.5281/zenodo.23609295`）。
>
"""

h = io.open("HANDOFF.md", encoding="utf-8").read()
if "修完 A1 / Paper A 投稿包陈旧问题" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    h = h[:j + 1] + "\n" + entry + h[j + 1:]
    io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h)
    print("handoff updated")

m = io.open("文件地图.md", encoding="utf-8").read()
row = ("156. 🔧 **2026-10-24 14:05 —— A1 / Paper A 包刷新**：A1 包 58→64 页、Paper A 包 70→74 页；"
       "旧包归档 `SUBMISSION/_archive/*_package_2026-10-18/`；六稿审计全 READY(A)；脚本 `tools/_p1576_refresh_a1_papera_packages.py`。\n")
if "A1 / Paper A 包刷新" not in m:
    i = m.find("155. 🔖 **Zenodo v2.3 DOI")
    if i < 0:
        i = m.find("154. 🏷️ **GitHub v2.3")
    e = m.find("\n", i)
    m = m[:e + 1] + row + m[e + 1:]
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map updated")

note = ("| **A1** | `paper_a1/` | **64** | 2026-10-18 已投 PAA（Submission ID `0a4629f0-…`），"
        "**With editor（2026-10-19）**；包已按 64 页主稿刷新（2026-10-24），审计 **READY(A)** |")
old = None
for line in m.splitlines():
    if line.startswith("> | **A1** |"):
        old = line
        break
if old and old != note:
    m2 = m.replace(old, note, 1)
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m2)
    print("map A1 row updated")
old_pa = None
for line in m.splitlines():
    if line.startswith("> | **Paper A**（P1+P2）"):
        old_pa = line
        break
note_pa = ("| **Paper A**（P1+P2）| `paper合/` | **NC 74｜Springer 53** | 2026-10-18 投 Neurocomputing"
           "（`NEUCOM-D-26-23760`）→ **With Editor（2026-10-19）**；包已按 74 页主稿刷新（2026-10-24），审计 **READY(A)**；"
           "台账 96/96；provenance PASS |")
if old_pa and old_pa != note_pa:
    m2 = io.open("文件地图.md", encoding="utf-8").read().replace(old_pa, note_pa, 1)
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m2)
    print("map PaperA row updated")
print("done")