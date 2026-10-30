# -*- coding: utf-8 -*-
r"""Refresh the upload guide and record the retitle in the handoff document.

    python tools/_p655_record_retitle.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STAGE = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD"
MS = "P3_PRLETTERS-D-26-02378"
DOI = "10.5281/zenodo.23341223"
NEWTITLE = "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry"
OLDTITLE = ("Gradient Structure Laws as Predictors of PEFT Design: "
            "Zero-Shot Cross-Architecture Rank Allocation")

GUIDE = f"""UPLOAD THIS FOLDER ONLY
========================

Manuscript : {NEWTITLE}
Journal    : Pattern Recognition Letters
Id         : {MS}
Decision   : Revise

IMPORTANT - the title changed in this revision
----------------------------------------------
Old: {OLDTITLE}
New: {NEWTITLE}

The revision withdrew the claim that gradient structure predicts PEFT design, so the original
title no longer described the paper. A sentence explaining this has been appended to each of
the three response boxes; it is worth pasting it, because it shows the change came from the
review rather than from a mix-up.

Every file below is named with the manuscript id, so nothing else in this workspace can be
mistaken for it.

Editorial Manager slot                        file
--------------------------------------------  ----------------------------------------------
Manuscript (PDF)                              {MS}_Manuscript.pdf
Cover letter                                  {MS}_Cover_Letter.pdf
Supplementary material                        {MS}_Supplementary.pdf
Title page                                    {MS}_Title_Page.pdf
Highlights (PDF)                              {MS}_Highlights.pdf
Highlights (text, if the form wants text)     {MS}_Highlights.txt
LaTeX source (source file, not a PDF)         {MS}_LaTeX_Source.zip
Response to Reviewer 1 (paste into the box)   {MS}_Response_Reviewer1.txt
Response to Reviewer 2 (paste into the box)   {MS}_Response_Reviewer2.txt
Response to Reviewer 3 (paste into the box)   {MS}_Response_Reviewer3.txt

Form fields
-----------
Data availability : choose "Data is available in a public repository"
Repository DOI    : {DOI}
Highlights        : 5 bullets, each within the 85-character limit

Note on author details
----------------------
{MS}_Title_Page.pdf carries the author name, affiliation, e-mail and ORCID, because a title
page is where the journal requires the corresponding author's address. The highlights
deliberately carry no author details.

DO NOT UPLOAD
-------------
- main_full.pdf            (the 13-page archival version; not the submission)
- any .bak_* file          (moved to SUBMISSION/_superseded_P3_PRL_revision/)
- SUBMISSION/_superseded_* (the first submission of 2026-09-26, and this revision's backups)
- anything from another manuscript's folder: A1, A23 and PaperA all contain a file called
  main.pdf or Manuscript.pdf

Verified before staging
-----------------------
- Manuscript.pdf      10 pages, 0 LaTeX errors, carries the new title and the DOI
- Cover_Letter.pdf     2 pages, 0 LaTeX errors, carries the new title and the DOI
- Supplementary.pdf    5 pages, 0 LaTeX errors
- Highlights.pdf       5 bullets, all within 85 characters, no withdrawn claims, no author name
- Title_Page.pdf       2 pages, new title
- LaTeX source         extracted to a clean directory it compiles standalone (3 passes, 0
                       errors, 10 pages)
- response files       plain text, no LaTeX, no markdown emphasis, no placeholders
"""

ENT = f"""> **🏷️ 2026-10-14 14:00 —— 标题改为「{NEWTITLE}」（操作者选 A）；并查出 highlights 是重大隐患**
>
> ### 一、操作者裁决
>
> 在 A–F 六个候选里选 **A**：
> **{NEWTITLE}**（67 字符 / 7 词，符合指南"concise and informative、避免缩写与公式"）。
>
> **为何必须改**：原标题 *"…as **Predictors** of PEFT Design"* 承诺"Γ 能预测 PEFT 设计"，
> **而修订撤回了该主张** ⇒ **标题与内容不符**。新标题只声称**做得到的那件事**（从梯度几何零样本跨架构分配 rank），**不声称优于基线**。
>
> ### 二、✅ 标题已同步到 **11 个交付件 + 8 处回复说明**
>
> | 类 | 文件 |
> |---|---|
> | 正文 | `main.tex`、`main_full.tex`、`main_10pp.tex`、源包 `main.tex` |
> | 附属件 | `supplementary.tex`、`title_page_prl.tex`、`highlights.tex` |
> | 投稿元数据 | `EM_form_fields.txt`、`PRL_submission/README.md` |
> | 对外文档 | `cover_letter_prl.tex`、`RELEASE_NOTES.md` |
> | 回复信 | **三个回复框 + 组合信共 8 个文件**各追加一段「Title. The title has changed from … to …」说明 |
>
> **说明的用意**（对操作者有利）：写明改标题**源于审稿**，而非投错稿：
> > *"The revision withdrew the claim that gradient structure predicts PEFT design, so the original title no longer described the paper."*
>
> ### 三、🔴 顺带查出 **highlights 是重大隐患**
>
> `highlights.txt` **从未随修订更新**，仍在宣传**已撤回的主张**：
>
> | 旧 highlights 文字 | 问题 |
> |---|---|
> | `the **unique** admissible allocation statistic` | 唯一性已撤回（需 R3′ 公理） |
> | `**A critical rank separates** safe, damaging and collapsing allocation regimes` | crossing 已降级为 **bracketed at r ∈ [5,6]**（置换 p = 0.100） |
> | `Counterfactual tests show the coupling **predicts allocation uncertainty**` | 30× 方差比已撤回（98.9% 是秩间方差） |
>
> **⇒ 若原样交上去，等于在 highlights 里重申我们刚撤回的三个结论。**
>
> **另两处**：`highlights.tex` 里印了**作者姓名与单位**（highlights 不是 title page）；
> 一条 bullet **87 字符**，**超过 PRL 的 ≤85 上限**。
>
> **✅ 已重做**（`tools/_p653`，**一份 bullet 列表派生两个文件，杜绝再次不一致**）：
>
> | # | bullet | 字符 |
> |---|---|---|
> | 1 | Cross-modal gradient coupling gives a canonical PEFT allocation statistic | 73 |
> | 2 | Requiring additivity is an axiom, not a consequence of block decomposability | 76 |
> | 3 | Measured on CLIP, it predicts a LLaVA rank allocation with no target gradient | 77 |
> | 4 | The allocation does not beat matched controls; we report that rather than hide it | 81 |
> | 5 | At matched budget, AdaLoRA reaches lower alignment energy than our allocation | 77 |
>
> **5 条、全部 ≤85、无作者信息、无撤回主张** ✅
>
> ### 四、✅ 我在这轮犯的两个错（已修）
>
> | # | 错 | 修 |
> |---|---|---|
> | 1 | 在 `paper_ieee/` 下编译 `supplementary.tex`，而它用相对路径 `../figures/…` ⇒ **编译失败** | 改为**在 `supplementary/` 目录内**编译 ⇒ 5 页 / 0 错误（`tools/_p650`） |
> | 2 | **上传区的副本是在改标题之前复制的** ⇒ 回复文件还是旧标题、也没有说明 | **全部从权威源重新暂存**并加"副本必须与源 sha256 一致"的断言（`tools/_p651`） |
>
> （另修正我自己的一个**检查口径错误**：把 JSON 通配写法 `runs[*]`、glob `main/*.json` 误判为 markdown 强调；
> 改为只匹配真正的 `**bold**` / `*word*`。）
>
> ### 五、✅ 全部重编译并通过
>
> | 件 | 页 | 错误 | 新标题 | 旧标题 |
> |---|---|---|---|---|
> | `main.pdf` | **10** | 0 | ✅ | 无 |
> | `cover_letter_prl.pdf` | 2 | 0 | ✅ | 无 |
> | `supplementary.pdf` | **5** | 0 | ✅ | 无 |
> | `title_page_prl.pdf` | 2 | 0 | ✅ | 无 |
> | `highlights.pdf` | 1 | 0 | ✅ | 无 |
> | **源包** | — | — | **解压独立编译 3 遍：0 错误 / 10 页** | — |
>
> ### 六、✅ 上传区现为 **11 个文件**（原 8 个 + Title page + Highlights ×2）
>
> | 字节 | 文件 |
> |---|---|
> | 414,938 | `…_Manuscript.pdf` |
> | 131,184 | `…_Cover_Letter.pdf` |
> | 266,021 | `…_Supplementary.pdf` |
> | 69,123 | `…_Title_Page.pdf` |
> | 51,358 | `…_Highlights.pdf` |
> | 411 | `…_Highlights.txt` |
> | 128,804 | `…_LaTeX_Source.zip` |
> | 8,759 / 8,471 / 26,825 | `…_Response_Reviewer{{1,2,3}}.txt` |
> | 2,178 | `README_UPLOAD.txt`（含标题变更说明与逐项对照表） |
>
> **作者信息仅出现在 Title page**（期刊要求通信作者地址在该页）；**highlights 不含**。
>
> ### 七、剩余
>
> ① **只打开 `UPLOAD\\`，按 `README_UPLOAD.txt` 上传 10 项**
> ② **粘三个回复框**（含末尾的标题变更说明）
> ③ **EM 表单**：标题改为新标题；Data availability 勾"数据在公开仓库中可用" + 填 `{DOI}`；highlights 用新的 5 条
> ④ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(STAGE / "README_UPLOAD.txt", "w", encoding="utf-8", newline="").write(GUIDE)
    print(f"  wrote {(STAGE / 'README_UPLOAD.txt').relative_to(REPO)}")
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "标题改为" in t and NEWTITLE in t:
        print("  handoff already records the retitle")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("标题改为", NEWTITLE, "highlights 是重大隐患", "87 字符", "重新暂存"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
