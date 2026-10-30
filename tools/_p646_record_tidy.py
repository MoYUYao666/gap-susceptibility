# -*- coding: utf-8 -*-
r"""Record the submission tidy in the handoff document.

    python tools/_p646_record_tidy.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🧹 2026-10-14 13:00 —— 按操作者要求清理上传区（"我怕开错了"）**
>
> ### 一、操作者担心的问题（**实测成立**）
>
> | 槽位 | 工作区里的**同名候选数** |
> |---|---|
> | Manuscript PDF | **19 个**（`main.pdf` / `Manuscript.pdf` 分属 P1/P2/P3/A1/A23/PaperA…） |
> | Cover letter | **27 个** |
> | Supplementary | 3 个 |
>
> **⇒ 光看文件名必然传错。** 仅 P3 就有**两代**：`P3_PRL`（2026-09-26 已投版，463 KB）与
> `P3_PRL_revision`（现在这版，415 KB）—— **三个关键文件 sha256 全部不同**。
>
> ### 二、✅ 建立唯一上传暂存区
>
> ```
> SUBMISSION\\P3_PRL_revision\\UPLOAD\\
> ```
>
> **7 个文件 + 1 份指引，文件名全部带稿号 `P3_PRLETTERS-D-26-02378`** ⇒ 与工作区任何其它文件不可能混淆：
>
> | EM 槽位 | 文件 | 字节 | sha256 前 12 |
> |---|---|---|---|
> | Manuscript (PDF) | `..._Manuscript.pdf` | 414,996 | `d1b94c57ff7f` |
> | Cover letter | `..._Cover_Letter.pdf` | 131,744 | `e93c155601c6` |
> | Supplementary | `..._Supplementary.pdf` | 266,287 | `b4135c96b1aa` |
> | LaTeX source | `..._LaTeX_Source.zip` | 128,822 | `334473cf4f2e` |
> | Response R1/R2/R3 | `..._Response_Reviewer{{1,2,3}}.txt` | 8,232 / 7,944 / 26,298 | — |
> | 表单指引 | `README_UPLOAD.txt` | 2,178 | — |
>
> **✅ 逐个 sha256 核验：暂存件与权威源逐字节相同**（`tools/_p645`）。
>
> ### 三、✅ 已隔离的旧版（**不要打开**）
>
> | 目录 | 内容 |
> |---|---|
> | `SUBMISSION\\_superseded_P3_PRL_submitted_2026-09-26\\` | **首次投稿版**（原 `SUBMISSION\\P3_PRL\\`，28 个文件；含旧 manuscript/cover letter/latex_source/highlights/Title page） |
> | `SUBMISSION\\_superseded_P3_PRL_revision\\` | 本修订的 **11 个 `.bak_*`**（含从 `reviews/` 移出的 `_reviews_extracted.txt`） |
> | `SUBMISSION\\_old\\` | 更早的其它稿件投稿包 |
>
> **修订包内 `.bak` / 临时文件残留 = 0** ✅
>
> **⚠️ 顺带清掉一个容易误读的文件**：`reviews/_reviews_extracted.txt` 只是审稿 PDF 的 `pdftotext` 转储
> （前 9,888 字符与 `PRLETTERS-D-26-02378-reviews.pdf` 的抽文本**完全一致**）⇒ 移入 `_superseded_...`。
> `reviews/` 现在只剩**两个真正来源**：`PRL Revison.txt` 与 `PRLETTERS-D-26-02378-reviews.pdf`。
>
> ### 四、✅ 暂存件的质量复核（`tools/_p645`，全通过）
>
> | 检查 | 结果 |
> |---|---|
> | DOI `10.5281/zenodo.23341223` 在 | ✅ |
> | 旧 DOI `23341083` 不在 | ✅ |
> | 被取代的 `3607` / `2241` 不在 | ✅ |
> | 当前 `2344` / `1477` 在 | ✅ |
> | `p = 0.21` 在 | ✅ |
> | LaTeX 日志页数 | **10 页** |
>
> ### 五、⚠️ 仍是**待操作者决定**的两项（我未擅自搬入 `UPLOAD/`）
>
> | 项 | 现状 | 为何不擅自处理 |
> |---|---|---|
> | **Title page with declarations** | 首次投稿版在 `_superseded_P3_PRL_submitted_2026-09-26\\`（70 KB，2026-09-26） | **不确定 EM 是否要求重传**，也不确定作者/单位/声明是否需随修订更新 |
> | **Highlights** | 同上目录（`.pdf`/`.docx`/`.tex`/`.txt`） | **修订后摘要与结论有改动**（撤回 4 项主张）⇒ **需确认是否按新结论改一条**；PRL 要求 3–5 条、每条 ≤85 字符 |
>
> ### 六、其他文档同步
>
> - `SUBMISSION\\P3_PRL_revision\\UPLOAD_CHECKLIST.md` —— **重写**为指向 `UPLOAD/`
> - `文件地图.md` —— 顶部新增「🔴 上传暂存区（2026-10-14 新增）」节
>
> ### 七、剩余
>
> ① **只打开 `UPLOAD\\`，按 `README_UPLOAD.txt` 的表格逐项上传**
> ② **粘三个回复框**（`..._Response_Reviewer{{1,2,3}}.txt`）
> ③ **EM 表单**：Data availability 勾"数据在公开仓库中可用" + 填 `10.5281/zenodo.23341223`
> ④ 决定 Title page / Highlights 是否重传
> ⑤ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "按操作者要求清理上传区" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("按操作者要求清理上传区", "UPLOAD", "19 个", "27 个", "待操作者决定"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
