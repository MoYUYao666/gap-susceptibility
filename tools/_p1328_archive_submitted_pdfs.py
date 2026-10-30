# -*- coding: utf-8 -*-
r"""Archive the exact PDFs that were submitted, so that rebuilding the local working copies cannot overwrite them.

  SUBMISSION/_frozen_submitted/
      A1_PAA/          Manuscript.pdf, Title Page.pdf, Cover Letter.pdf, Graphical Abstract.pdf
      PaperA_NEUCOM/   Manuscript.pdf, Abstract.pdf, Cover Letter.pdf, Highlights.pdf
      P3_PRL_R1/       Manuscript.pdf, Supplementary.pdf, Cover Letter.pdf, Highlights.pdf
      SHA256SUMS.txt   sha256 of every archived file
      README.md        what these files are and why the local working copies now differ

The local manuscripts already carry the 2026-10-19 revision citations; the submission packages themselves are unchanged.

    python tools/_p1328_archive_submitted_pdfs.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "SUBMISSION", "_frozen_submitted")

GROUPS = {
    "A1_PAA": [
        ("SUBMISSION/A1_PatternAnalysisApplications/Manuscript.pdf", "Manuscript.pdf"),
        ("SUBMISSION/A1_PatternAnalysisApplications/Title Page.pdf", "Title Page.pdf"),
        ("SUBMISSION/A1_PatternAnalysisApplications/Cover Letter.pdf", "Cover Letter.pdf"),
        ("SUBMISSION/A1_PatternAnalysisApplications/Graphical Abstract.pdf", "Graphical Abstract.pdf"),
    ],
    "PaperA_NEUCOM": [
        ("SUBMISSION/PaperA_Neurocomputing/Manuscript.pdf", "Manuscript.pdf"),
        ("SUBMISSION/PaperA_Neurocomputing/Abstract.pdf", "Abstract.pdf"),
        ("SUBMISSION/PaperA_Neurocomputing/Cover Letter.pdf", "Cover Letter.pdf"),
        ("SUBMISSION/PaperA_Neurocomputing/Highlights.pdf", "Highlights.pdf"),
    ],
    "P3_PRL_R1": [
        ("SUBMISSION/P3_PRL_revision/UPLOAD/P3_PRLETTERS-D-26-02378_Manuscript.pdf", "Manuscript.pdf"),
        ("SUBMISSION/P3_PRL_revision/UPLOAD/P3_PRLETTERS-D-26-02378_Supplementary.pdf", "Supplementary.pdf"),
        ("SUBMISSION/P3_PRL_revision/UPLOAD/P3_PRLETTERS-D-26-02378_Cover_Letter.pdf", "Cover Letter.pdf"),
        ("SUBMISSION/P3_PRL_revision/UPLOAD/P3_PRLETTERS-D-26-02378_Highlights.pdf", "Highlights.pdf"),
    ],
}

README = """# 投出版 PDF 归档（frozen submitted PDFs）

本目录保存 **2026-10-18 实际投出**的 PDF（逐文件复制），目的是让后续修改本地工作稿时**不会覆盖投出版**。

| 子目录 | 期刊 / 投稿 | 说明 |
|---|---|---|
| `A1_PAA/` | Pattern Analysis and Applications（Submission received，技术检查中）| Manuscript 58 页（投出版）＋ Title Page ＋ Cover Letter ＋ Graphical Abstract |
| `PaperA_NEUCOM/` | Neurocomputing `NEUCOM-D-26-23760` | Manuscript 70 页（投出版）＋ Abstract ＋ Cover Letter ＋ Highlights |
| `P3_PRL_R1/` | PRL `PRLETTERS-D-26-02378R1`（在审，deadline 2026-11-02）| Manuscript ＋ Supplementary ＋ Cover Letter ＋ Highlights（UPLOAD 原样）|

## 为什么单独归档

2026-10-19 的周检之后，**本地工作稿**已补入修回用引用（A1 59 页；Paper A NC 70 / Springer 50；P3 10 页），
`SUBMISSION/` 下的投稿包保持投出状态不变。为了让"投出的 PDF 到底是哪一版"永远可查、不被重建覆盖，
这里再存一份**不可变副本**，并在 `SHA256SUMS.txt` 里记录每个文件的哈希。

## 校验

```powershell
cd SUBMISSION/_frozen_submitted
Get-Content SHA256SUMS.txt | ForEach-Object { $h,$p = $_ -split '  '; (Get-FileHash $p -Algorithm SHA256).Hash -eq $h }
```

生成脚本：`tools/_p1328_archive_submitted_pdfs.py`（幂等；只复制、不改动源文件）。
"""


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    plan = []
    for group, items in GROUPS.items():
        for src_rel, name in items:
            src = os.path.join(REPO, src_rel)
            if not os.path.exists(src):
                print(f"  !! missing {src_rel}")
                continue
            plan.append((group, src, name))
    print(f"  files to archive: {len(plan)}")
    for group, src, name in plan:
        print(f"   {group}/{name}  <- {os.path.relpath(src, REPO)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    lines = []
    for group, src, name in plan:
        dst_dir = os.path.join(OUT, group)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, name)
        shutil.copyfile(src, dst)
        lines.append(f"{sha256(dst)}  {group}/{name}")
        print(f"  archived {group}/{name}")
    io.open(os.path.join(OUT, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="").write(README)
    print(f"  wrote SHA256SUMS.txt ({len(lines)} files) and README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
