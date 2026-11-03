# -*- coding: utf-8 -*-
r"""Record the DOI insertion in the handoff document, and list the files to re-upload.

Operator supplied the DOI on 2026-10-14: 10.5281/zenodo.23341083

    python tools/_p627_record_doi.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
OUT = REPO / "outputs" / "analysis" / "doi_upload_list.json"
DOI = "10.5281/zenodo.23341083"

ENT = f"""> **🔗 2026-10-14 10:00 —— Zenodo DOI 已取得并填入全部位置（`{DOI}`）**
>
> ### 一、操作者提供
>
> > **"DOI: {DOI}"**
>
> ### 二、✅ 关键前提已满足：**仓库已由操作者改为 Public**
>
> `gh repo view` 实测 **`isPrivate: false` / `visibility: PUBLIC`** ⇒
> **Zenodo 的 DOI 落地页匿名可访问**，满足 PRL Guide 的 research-data Option C（"归档到仓库并给出持久标识"）。
>
> ### 三、✅ DOI 已填入 **5 处代码/文档 + 4 份操作者文档**
>
> | # | 位置 | 改法 |
> |---|---|---|
> | 1 | `paper3/paper_ieee/main.tex` Data statement | 删掉"仓库私有、录用后再存档" ⇒ 改为**公开仓库 URL + Zenodo DOI** |
> | 2 | `SUBMISSION/P3_PRL_revision/manuscript/latex_source/main.tex` | 同上（源包副本） |
> | 3 | `paper3/paper_ieee/cover_letter_prl.tex` | `[REPOSITORY DOI, to be inserted]` ⇒ 实际 DOI + `\\url` |
> | 4 | `publish_clean/README.md` | Data availability 加 **Zenodo DOI 徽章** + 明示"应引用的持久标识" |
> | 5 | `README.md`（仓库根） | 同上 |
> | 6 | `SUBMISSION/P3_PRL_revision/README.md`、`ARCHIVE_WITH_ZENODO.md`、`UPLOAD_CHECKLIST.md` | 追加「DOI 已取得」节 |
> | 7 | `paper3/paper_ieee/PRL_submission/EM_author_classifications.txt` | **修正过期指引**：原文说"没有 DOI ⇒ 不能选公开仓库" ⇒ 追加 2026-10-14 更新，**改为应勾选"数据在公开仓库中可用"** |
>
> ### 四、✅ 重编译与核验
>
> | 文件 | 页数 | 错误 | 未定义 | DOI 在 PDF 内 |
> |---|---|---|---|---|
> | `main.pdf` | **10** | **0** | **0** | ✅（DOI + URL 均完整） |
> | `cover_letter_prl.pdf` | 2 | **0** | **0** | ✅ |
>
> 核验脚本 `tools/_p622`：**从 PDF 抽文本**复核（不是只看源码）。
>
> ### 五、🔴 我在这轮犯的一个错（已修）：**源包被我做残了**
>
> 第一次重打 `P3_latex_source_revision.zip` 时我只装了 4 个文件（6,775 字节）——
> **漏了 `sections/` 六个分节与两张图** ⇒ **该包根本无法编译**（原包 48,879 字节）。
> **⇒ 已按 `main.tex` 的依赖重建（`tools/_p624`）**：
>
> ```
> main.tex  sections/{{introduction,related_work,theory,experiments,discussion,conclusion}}.tex
> references.bib  main.bbl  figures/{{fig1_phase_transition,fig2_counterfactual}}.png
> README_compile.txt                       = 12 个成员 / 128,816 字节
> ```
> **⇒ 并做"解压到干净目录独立编译"验证（`tools/_p625`）**：
> **3 遍 pdflatex，0 错误，10 页，产出 `main.pdf` 414,995 字节 —— 与正式版字节数完全一致** ✅
>
> **⚠️ 教训：说"重打源包"必须验证"解压后能否独立编译"，不能只看 zip 里有没有 `main.tex`。**
> 顺带清掉了混进 `latex_source/` 的 3 个 `.bak_*`（编辑部的包里不该有备份文件）。
>
> ### 六、⚠️ 待重新上传 EM 的文件清单
>
> | 文件 | 路径 | 大小 | 状态 |
> |---|---|---|---|
> | **Manuscript (PDF)** | `SUBMISSION/P3_PRL_revision/manuscript/main.pdf` | 414,995 | 🔄 **需重传**（Data statement 改了） |
> | **Cover letter** | `SUBMISSION/P3_PRL_revision/manuscript/cover_letter.pdf` | 131,743 | 🔄 **需重传**（DOI 填了） |
> | **LaTeX source** | `SUBMISSION/P3_PRL_revision/manuscript/P3_latex_source_revision.zip` | 128,816 | 🔄 **需重传**（重建过） |
> | Supplementary | `SUBMISSION/P3_PRL_revision/manuscript/supplementary.pdf` | 266,287 | ⏸ **未改动**（无 Data statement） |
> | Title page with declarations | `SUBMISSION/P3_PRL_revision/manuscript/` 若有 | — | ⏸ 未改动 |
> | Highlights | 同上 | — | ⏸ 未改动 |
> | **Response to reviewers**（三个回复框） | `SUBMISSION/P3_PRL_revision/response/P3_RESPONSE_Reviewer{{1,2,3}}_plain.txt` | — | ⏸ 待粘贴 |
>
> ### 七、✅ GitHub 侧
>
> | 项 | 值 |
> |---|---|
> | 提交 | **`8b03800`**（`c42c6e8..8b03800`） |
> | 远端 README | **5,867 字符**，**含 DOI 与徽章** ✅ |
> | tag | 已重打到 `8b03800` |
> | Release | 已重建：`isDraft: false`、`Latest` |
> | 可见性 | **PUBLIC** |
>
> **Zenodo DOI**：`{DOI}` ⇒ https://doi.org/{DOI}
> **Release**：https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v1.0-prl-revision
>
> ### 八、剩余
>
> ① **重传 EM**：稿件 PDF + cover letter + LaTeX 源包（上表前三项）
> ② **EM 三个回复框**（粘贴 `P3_RESPONSE_Reviewer{{1,2,3}}_plain.txt`）
> ③ **EM 表单**：Data availability 勾"数据在公开仓库中可用" + 填 DOI
> ④ `p3d_summary.json` 指纹更新（非阻塞）
> ⑤ 提交
"""


def upload_list() -> list[dict]:
    items = [
        ("manuscript/main.pdf", "Manuscript (PDF)", True),
        ("manuscript/cover_letter.pdf", "Cover letter", True),
        ("manuscript/P3_latex_source_revision.zip", "LaTeX source package", True),
        ("manuscript/supplementary.pdf", "Supplementary material", False),
    ]
    rows = []
    for rel, label, changed in items:
        p = PKG / rel
        rows.append({"file": rel, "label": label, "bytes": p.stat().st_size if p.exists() else None,
                     "exists": p.exists(), "needs_reupload": changed})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rows = upload_list()
    print("  Files for EM:")
    for r in rows:
        flag = "RE-UPLOAD" if r["needs_reupload"] else "unchanged "
        print(f"    {flag} {r['label']:<24} {r['bytes'] or 0:>9,} bytes  {r['file']}")
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "Zenodo DOI 已取得并填入全部位置" in t:
        print("  handoff already recorded")
    else:
        i = t.find("# 项目交接文档")
        j = t.find("\n", i)
        io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
        t2 = io.open(hp, encoding="utf-8").read()
        for k in ("Zenodo DOI 已取得并填入全部位置", DOI, "8b03800", "源包被我做残了",
                  "SOURCE PACKAGE COMPILES STANDALONE" if False else "独立编译"):
            print(f"    {'OK ' if k in t2 else 'BAD'} {k}")
        print(f"    HANDOFF lines = {len(t2.splitlines())}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps({"doi": DOI, "files": rows}, ensure_ascii=False, indent=1))
    print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
