# -*- coding: utf-8 -*-
r"""Record the DOI across the remaining operator-facing documents.

The DOI is already in: main.tex (Data statement), the source-package copy of main.tex, the
cover letter, and both READMEs. This updates the documents that still describe the archive
as "pending":

- SUBMISSION/P3_PRL_revision/README.md          status and DOI
- SUBMISSION/P3_PRL_revision/ARCHIVE_WITH_ZENODO.md   mark the plan DONE, give the DOI
- SUBMISSION/P3_PRL_revision/UPLOAD_CHECKLIST.md      tick the DOI item
- paper3/paper_ieee/PRL_submission/EM_author_classifications.txt
      this file tells the operator which data-availability option to tick, and it currently
      says there is no DOI - which is now false and would lead to the wrong option

    python tools/_p626_record_doi_docs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
DOI = "10.5281/zenodo.23341083"
URL = f"https://doi.org/{DOI}"
GH = "https://github.com/MoYUYao666/gap-susceptibility"

BLOCK = f"""
---

## ✅ DOI 已取得（2026-10-14）

| 项 | 值 |
|---|---|
| **DOI** | **`{DOI}`** |
| **解析地址** | {URL} |
| **公开仓库** | {GH}（**已由操作者改为 Public**） |
| **归档版本** | `v1.0-prl-revision` |

**⇒ 三处已填入**：① 稿件 Data statement ② cover letter ③ README 的 Data availability。
**⇒ EM 表单的 Data availability 一栏现在可以选"数据在公开仓库中可用"**（此前不能选，因为没有 DOI）。
"""


def append(p: Path, marker: str, block: str, label: str) -> bool:
    if not p.exists():
        print(f"  MISSING  {label}")
        return False
    t = io.open(p, encoding="utf-8", errors="replace").read()
    if marker in t:
        print(f"  already  {label}")
        return True
    print(f"  append   {label}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    targets = [
        (PKG / "README.md", "DOI 已取得", "package README.md"),
        (PKG / "ARCHIVE_WITH_ZENODO.md", "DOI 已取得", "ARCHIVE_WITH_ZENODO.md"),
        (PKG / "UPLOAD_CHECKLIST.md", "DOI 已取得", "UPLOAD_CHECKLIST.md"),
    ]
    for p, marker, label in targets:
        append(p, marker, BLOCK, label)
    print()
    if not a.apply:
        print("  (dry run)")
        return 0
    for p, marker, label in targets:
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if marker in t:
            continue
        bak = p.with_suffix(p.suffix + ".bak_p626")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + BLOCK)

    # EM option guidance: the stale claim must be corrected, not left to mislead
    em = REPO / "paper3" / "paper_ieee" / "PRL_submission" / "EM_author_classifications.txt"
    if em.exists():
        t = io.open(em, encoding="utf-8", errors="replace").read()
        note = f"""

{'=' * 70}
⚠️ 2026-10-14 更新（此段为重述，上方原文保留，但结论已变）
{'=' * 70}
上文第 3 条写"目前没有公开仓库/DOI"——**该结论已于 2026-10-14 过期**：
  · 公开仓库：{GH}（已 Public）
  · Zenodo DOI：{DOI}（{URL}）
⇒ **EM 表单的 Data availability 一栏，现在应当勾选"数据在公开仓库中可用"
  （"Data is available in a public repository"）**，并在 Data linking 处填 DOI。
  **不再适用"按请求提供"这一项**（该项在数据实际已公开时会构成低报）。
"""
        if "2026-10-14 更新" not in t:
            bak = em.with_suffix(em.suffix + ".bak_p626")
            if not bak.exists():
                shutil.copy2(em, bak)
            io.open(em, "w", encoding="utf-8", newline="").write(t.rstrip() + note)
            print(f"  append   EM_author_classifications.txt (option guidance corrected)")

    print()
    print("  Re-check:")
    for p, marker, label in targets:
        t = io.open(p, encoding="utf-8", errors="replace").read() if p.exists() else ""
        print(f"    {label:<30} DOI present: {DOI in t}")
    t = io.open(em, encoding="utf-8", errors="replace").read() if em.exists() else ""
    print(f"    {'EM_author_classifications.txt':<30} DOI present: {DOI in t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
