# -*- coding: utf-8 -*-
"""Record the DOI / abstract / Commentary-headroom round (non-P3 manuscripts)."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

entry = """> **🔖 2026-10-24 15:00 —— 四篇工作副本改引 v2.3 DOI；A1 摘要压到 241 词；Commentary 留出页余量**
>
> - **DOI 更新**（`tools/_p1583_update_doi_to_v23.py`，逐条断言、幂等；**已投出/冻结包未动**）：
>   `paper合/main_nc.tex`、`paper合/main_springer.tex`、`paper_a1/main.tex`、`paper_a1/title_page.tex`、
>   `paper_a2/main_ieee.tex`、`paper_review_prl/MANUSCRIPT.md` 及四封 cover letter（工作副本）
>   由 v1.0 `10.5281/zenodo.23341223` 改为 **v2.3 `10.5281/zenodo.23609295`**；
>   Paper A 的措辞同步改为"v2.3（2026-10-24）已含附录 E/G 的 decoder 逐 run 记录，适配器不分发"——**镜像实测确实含 13 个 LLaVA + 53 个 Qwen JSON**（无 `.pt`）；
>   A23 的"仓库当前私有、发表后公开"过期表述改为"公开仓库 + v2.3 Zenodo 快照"；
> - **一致性门禁同步**：`tools/_p1181_verify_paperA_consistency.py` 原要求 v1.0 时代的措辞
>   "Sections E and G were produced after that snapshot"；现改为要求 v2.3 DOI + "includes the decoder-model records…" + "adapters are not redistributed"，
>   复核 **0 failure**；
> - **A1 摘要**：249 → **241 词**（限 250，余量 9 词），只删冗词不动数据：`every prediction`→`predictions`、
>   `the error it can hide is bounded…small enough for the intervention to flip`→`the hidden error is bounded…small enough to flip`、
>   `reproduces the shape of the measured curve`→`reproduces the curve's shape`；
> - **Commentary 页余量**：`MANUSCRIPT.md` 精简 **4034 → 3952 词（−82）**，只并合重复表述（不改任何主张/清单/引用）；
>   重建后仍 **7 页**、末页行数 **126 → 118**、0 error / 0 undefined / 0 overfull、清单 12 项、关键词 6；
> - **重建与刷新**：Paper A NC **74 页**、Springer **53 页**、A1 **64 页**、A23 **70 页**（页数均未变，0/0/0）；
>   `_p1576` 刷新 A1/Paper A 包（新增 Title Page 同步、A1 摘要词数写入 README）；
>   `tools/_p1445_rebuild_packages.py --apply` 重建五份"下一次投稿"包（`SUBMISSION/_venue_builds/*_next`）；
> - **门禁**：六 profile **READY(A)、0 fail / 0 warn**；台账 96/96、A1 216/216、Paper A 88/88；工作树已提交（`621d809`）。
>
"""

h = io.open("HANDOFF.md", encoding="utf-8").read()
if "四篇工作副本改引 v2.3 DOI" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    h = h[:j + 1] + "\n" + entry + h[j + 1:]
    io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h)
    print("handoff updated")

m = io.open("文件地图.md", encoding="utf-8").read()
row = ("160. 🔖 **2026-10-24 15:00 —— 四篇改引 v2.3 DOI**：Paper A/A1/A23/Commentary 工作副本 DOI 改为 "
       "`10.5281/zenodo.23609295`；A1 摘要 249→241 词；Commentary −82 词（末页 126→118 行）；`*_next` 包已重建。\n")
if "四篇改引 v2.3 DOI" not in m:
    i = m.find("159. 🔤 **2026-10-24 14:35")
    e = m.find("\n", i)
    m = m[:e + 1] + row + m[e + 1:]
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map updated")
print("done")