# -*- coding: utf-8 -*-
r"""Finish the tidy: move the extracted reviews text out, refresh the checklists.

Operator: "清理一下，我怕开错了"

- reviews/_reviews_extracted.txt is only a pdftotext dump of the review PDF (the first 9,888
  characters are identical to the PDF's text). It sits in the reviews/ folder under a name
  that invites confusion with the actual reviews, so it is moved to the superseded area.
- UPLOAD_CHECKLIST.md is rewritten to point at the new UPLOAD/ staging folder.
- 文件地图.md is updated: the tools package moved and the staging folder is new.

    python tools/_p644_finish_tidy.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
SUP = REPO / "SUBMISSION" / "_superseded_P3_PRL_revision"
MAP = REPO / "文件地图.md"

NOTE = """# 上传暂存区已建立（2026-10-14）

**操作者要求**：「清理一下，我怕开错了」

## 一、只需打开这个文件夹

```
SUBMISSION\\P3_PRL_revision\\UPLOAD\\
```

里面的 7 个文件**文件名都带稿号 `P3_PRLETTERS-D-26-02378`**，
所以工作区里任何其它 `main.pdf` / `Manuscript.pdf` / `Cover Letter.pdf` **都不可能被误当成它**。

| EM 槽位 | 文件 |
|---|---|
| Manuscript (PDF) | `P3_PRLETTERS-D-26-02378_Manuscript.pdf` |
| Cover letter | `P3_PRLETTERS-D-26-02378_Cover_Letter.pdf` |
| Supplementary material | `P3_PRLETTERS-D-26-02378_Supplementary.pdf` |
| LaTeX source | `P3_PRLETTERS-D-26-02378_LaTeX_Source.zip` |
| Response to Reviewer 1/2/3 | `P3_PRLETTERS-D-26-02378_Response_Reviewer{1,2,3}.txt` |
| （表单指引） | `README_UPLOAD.txt` |

## 二、已隔离的旧版（**不要打开、不要上传**）

| 目录 | 是什么 |
|---|---|
| `SUBMISSION\\_superseded_P3_PRL_submitted_2026-09-26\\` | **2026-09-26 首次投稿的那一版**（原 `SUBMISSION\\P3_PRL\\`）—— 含旧 `manuscript.pdf`（463 KB）、旧 cover letter、旧 `latex_source.zip`（205 KB）、highlights、Title page |
| `SUBMISSION\\_superseded_P3_PRL_revision\\` | 本修订过程中产生的 **10 个 `.bak_*` 备份** |
| `SUBMISSION\\_old\\` | 更早的其它稿件投稿包 |

**⚠️ 为什么必须隔离**：工作区里叫 `main.pdf` 的有 **19 个**、叫 cover letter 的有 **27 个**
（分属 P1/P2/P3/A1/A23/PaperA 等多个项目）。**光看文件名必然传错。**

## 三、仍然是**待操作者决定**的两项

| 项 | 现状 |
|---|---|
| **Title page with declarations** | 首次投稿版在 `_superseded_P3_PRL_submitted_2026-09-26\\Title page with declarations.pdf`（70 KB，2026-09-26）。**若 EM 要求重传，需要确认它是否仍与修订稿一致**（作者、单位、声明） |
| **Highlights** | 同上目录有 `highlights.pdf` / `.docx` / `.tex` / `.txt`（2026-09-26）。**PRL 要求 3–5 条、每条 ≤85 字符**；修订后摘要与结论有改动 ⇒ **需确认是否要按新结论改一条** |

**（这两项我未擅自搬入 `UPLOAD/`，因为不确定 EM 是否要求重传、也不确定内容是否需随修订更新。）**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    src = PKG / "reviews" / "_reviews_extracted.txt"
    dst = SUP / "reviews" / "_reviews_extracted.txt"
    print(f"  move {src.relative_to(REPO)}")
    print(f"    -> {dst.relative_to(REPO)}")
    cl = PKG / "UPLOAD_CHECKLIST.md"
    print(f"  rewrite {cl.relative_to(REPO)} (points at UPLOAD/)")
    print(f"  update  {MAP.name}")
    if not a.apply:
        print("  (dry run)")
        return 0
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    io.open(cl, "w", encoding="utf-8", newline="").write(NOTE)
    t = io.open(MAP, encoding="utf-8", errors="replace").read()
    marker = "## 🔴 上传暂存区（2026-10-14 新增）"
    if marker not in t:
        block = f"""{marker}

**操作者要求**：「清理一下，我怕开错了」⇒ **只打开 `SUBMISSION\\P3_PRL_revision\\UPLOAD\\`**。

- 里面 7 个文件**文件名都带稿号 `P3_PRLETTERS-D-26-02378`** ⇒ 与工作区其它 `main.pdf` 不可能混淆
- **已隔离的旧版**：`SUBMISSION\\_superseded_P3_PRL_submitted_2026-09-26\\`（首次投稿版）、
  `SUBMISSION\\_superseded_P3_PRL_revision\\`（10 个 `.bak_*`）、`SUBMISSION\\_old\\`（更早稿件）
- **待操作者决定**：`Title page with declarations` 与 `Highlights` 是否随修订重传（首次投稿版在 `_superseded_...` 里）
- 明细见 `SUBMISSION\\P3_PRL_revision\\UPLOAD_CHECKLIST.md` 与 `UPLOAD\\README_UPLOAD.txt`

"""
        i = t.find("\n", t.find("# "))
        t = t[:i + 1] + "\n" + block + t[i + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(t)
    print()
    print("  Re-check:")
    print(f"    reviews/ now: "
          f"{[p.name for p in (PKG / 'reviews').iterdir() if p.is_file()]}")
    print(f"    UPLOAD/ now : "
          f"{len([p for p in (PKG / 'UPLOAD').iterdir() if p.is_file()])} files")
    print(f"    {MAP.name} contains the marker: {marker in io.open(MAP, encoding='utf-8').read()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
