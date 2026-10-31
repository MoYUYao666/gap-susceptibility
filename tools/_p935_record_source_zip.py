# -*- coding: utf-8 -*-
r"""Record the rebuilt LaTeX source archive in the upload folder and the handoff.

    python tools/_p935_record_source_zip.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REV = REPO / "SUBMISSION" / "P3_PRL_revision"
UPLOAD = REV / "UPLOAD_2026-10-15"
ZIP = UPLOAD / "P3_PRLETTERS-D-26-02378_LaTeX_Source.zip"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "LaTeX 源码包已重建"

NOTE = """
The LaTeX source archive
------------------------

  P3_PRLETTERS-D-26-02378_LaTeX_Source.zip   17 entries

It replaces the archive uploaded on 2026-10-13 and is rebuilt from the current sources, because the
manuscript and the supplement have both changed since then (section pointers, corollary numbering,
theorem spacing, table layout, the added sample-size table). Contents:

  README_compile.txt, main.tex, main.bbl, references.bib
  sections/{introduction,related_work,theory,experiments,discussion,conclusion}.tex
  figures/{fig1_phase_transition,fig2_counterfactual}.png
  supplementary/{supplementary.tex, supplementary.bbl, references.bib}
  supplementary/figures/{fig3_ers,fig4_E_trajectory}.png

Checks run on it: every member is byte-identical to its source file in the working tree; the archive is
CRC-clean; and extracting it into an empty folder and compiling there gives main.pdf 10 pages and
supplementary.pdf 6 pages with 0 errors and no undefined references or citations.

Note: fig4_E_trajectory.png is carried over from the previous archive even though no current .tex
includes it. That was also true of the submitted archive, so it is preserved rather than dropped.

Note: compiling the supplement prints "Font shape `OT1/ptm/m/scit' undefined" once. This is a font
substitution warning (small-caps italic Times, used by \\emph inside a table caption) and does not
affect the text or the PDF.
"""

ENT = """> **🗜️ 2026-10-15 15:00 —— P3 的 LaTeX 源码包已重建（同样要重传）**
>
> 操作者指出：**「latexsource也需要重传」**——正确。10-13 上传的
> `P3_PRLETTERS-D-26-02378_LaTeX_Source.zip`（17 条目）**已经是旧源码**：此后正文与补充材料都改过
> （节指针、corollary 编号、定理头排版、表格排布、新增样本量表），若只换 PDF 不换源码，
> **期刊手上会是一份与 PDF 对不上的源码**。
>
> ### 一、✅ 重建结果
>
> `SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/P3_PRLETTERS-D-26-02378_LaTeX_Source.zip`
> —— **17 条目 / 228,916 字节**，布局与投稿版一致：
>
> ```
> README_compile.txt  main.tex  main.bbl  references.bib
> sections/{introduction,related_work,theory,experiments,discussion,conclusion}.tex
> figures/{fig1_phase_transition,fig2_counterfactual}.png
> supplementary/{supplementary.tex, supplementary.bbl, references.bib}
> supplementary/figures/{fig3_ers,fig4_E_trajectory}.png
> ```
>
> ### 二、✅ 三项自检（`tools/_p933`）
>
> | 检查 | 结果 |
> |---|---|
> | 包内每个成员 vs 工作区源文件 | **逐字节一致**（SHA-256 比对 16 个成员）|
> | 压缩包完整性 | `testzip()` **通过** |
> | **解压到空目录后独立编译** | **main.pdf 10 页、supplementary.pdf 6 页，均 0 错误、0 未定义引用/引文** |
> | `README_compile.txt` | 新写：两份文档各自的 `pdflatex`/`bibtex` 顺序、依赖宏包、目录布局 |
>
> ### 三、⚠️ 两个如实记录的细节
>
> | 项 | 说明 |
> |---|---|
> | `fig4_E_trajectory.png` **当前没有任何 `.tex` 引用** | 但**投稿版也带着它**，故**原样保留**（不擅自删）|
> | 编译补充材料会打印 **1 条 `Font shape 'OT1/ptm/m/scit' undefined`** | 是**字体替换警告**（Times 小体大写斜体，用于表格 caption 里的 `\\emph`），**不影响文字与 PDF**；**未改稿件**以免产生新的源码差异 |
>
> ### 四、⚠️ 自查发现并修掉的一个**假门禁**
>
> 我最初的检查用 `log.count("undefined")` 判"未定义引用"——它**同时命中了那条字体警告**，
> 于是**在文档实际完全正常的情况下报"补充材料编译不干净"**，我按这个假信号查了三轮。
> 已改为**精确匹配** `LaTeX Warning: Reference/Citation ... undefined`。
> **教训**：门禁必须匹配它真正要检查的对象，宽泛的子串计数会制造假失败（与 `_reproducibility_gate.py` 那次假通过同源）。
>
> ### 五、✅ 待上传目录现状（5 件）
>
> | 文件 | 大小 |
> |---|---|
> | `P3_PRLETTERS-D-26-02378_Manuscript.pdf` | 416,070 B（= `main.pdf`）|
> | `P3_PRLETTERS-D-26-02378_Supplementary.pdf` | 270,586 B（= `supplementary.pdf`）|
> | `P3_PRLETTERS-D-26-02378_LaTeX_Source.zip` | **228,916 B（本次重建）** |
> | `main.pdf` / `supplementary.pdf` | 默认名副本 |
> | `README.md` | 已附源码包说明 |
>
> ⚠️ **申请文本**（`EMAIL_TO_EM_2026-10-15.txt`）里"替换两份文件"的措辞**需要更新为三份**
> （正文 + 补充材料 + **LaTeX 源码包**）；**已发出的 EM 查询不能编辑**，此更新供后续回复使用。
>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0

    assert ZIP.exists(), "the archive is missing"
    shutil.copy2(ZIP, REV / "CORRECTED_2026-10-15" / "P3_PRLETTERS-D-26-02378_LaTeX_Source.zip")
    for folder in (UPLOAD, REV / "CORRECTED_2026-10-15"):
        rp = folder / "README.md"
        if rp.exists() and "The LaTeX source archive" not in rp.read_text(encoding="utf-8"):
            with io.open(rp, "a", encoding="utf-8", newline="") as fh:
                fh.write(NOTE)
            print(f"  {folder.name}/README.md: source archive documented")

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("26. 🗜️ **P3 LaTeX 源码包已重建（2026-10-15 15:00）** —— "
           "`UPLOAD_2026-10-15/P3_PRLETTERS-D-26-02378_LaTeX_Source.zip`（**17 条目 / 228,916 B**，"
           "布局同投稿版）。三项自检：**成员与源逐字节一致**、CRC 通过、**解压后独立编译 main 10 页 + "
           "supplementary 6 页，0 错误 0 未定义引用**。⚠️ 待上传件由 2 件变 **3 件**（正文／补充／源码包）；"
           "申请文本待改为「三份」。⚠️ 自查发现**假门禁**：`count('undefined')` 会命中字体替换警告，"
           "已改精确匹配。详见 `HANDOFF.md` 顶部 2026-10-15 15:00 条目。\n")
    anchor = "25. ↕️ **补充材料表与表题间距已加开（2026-10-15 14:55）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")

    man = UPLOAD / "P3_PRLETTERS-D-26-02378_Manuscript.pdf"
    supp = UPLOAD / "P3_PRLETTERS-D-26-02378_Supplementary.pdf"
    print("  upload folder now holds:")
    for p in sorted(UPLOAD.iterdir()):
        print(f"    {p.name:<46} {p.stat().st_size:>9,} B")
    assert man.exists() and supp.exists() and ZIP.exists()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
