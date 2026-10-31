# -*- coding: utf-8 -*-
r"""Record the frozen-submitted-PDF archive and refresh the SUBMISSION index.

    python tools/_p1329_record_frozen_pdfs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
SUBREADME = REPO / "SUBMISSION" / "README.md"

HANDOFF_ENTRY = """> **🗄️ 2026-10-19 12:45 —— 投出版 PDF 归档（本地稿已含新增引用，投稿版单独冻结）**
>
> 按"**引用直接加进本地稿、投出版的 PDF 原样保留**"处理：
>
> | 项 | 状态 |
> |---|---|
> | 本地工作稿 | **已含**周检补引（A1 加 Sharma & Saxena 2026 / Yaras 2024；Paper A 升级 Amblard 期刊版 + 2 条 CLIP-CIL；P3 加 IFCLoRA / StatLoRA / LoRA-GA²）；A1 **59 页**、Paper A NC **70**/Springer **50**、P3 **10**，均 0/0/0 |
> | 投出版 PDF 归档 | 新建 `SUBMISSION/_frozen_submitted/`：**12 个 PDF**（A1 PAA 4 件、Paper A NEUCOM 4 件、P3 R1 4 件），逐文件 `SHA256SUMS.txt`（**校验 0 mismatch**），README 说明用途；生成脚本 `_p1328` |
> | 投稿包 | `SUBMISSION/` 三个包**一字未动**（A1 仍 58 页投出版；P3 R1 哈希不变）|
> | git 边界 | `SUBMISSION/` 全目录被 `.gitignore` 排除（发布边界策略）——归档**只存磁盘**，靠 SHA-256 清单固定，不强制入库 |
>
> A1 审计因此保留**预期内**的 `I-02`/`I-06`（包 58 页 vs 本地 59 页），已在 `docs/REVISION_CITATION_BACKLOG_2026-10-19.md` 说明。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0

    h = io.open(HANDOFF, encoding="utf-8").read()
    if "投出版 PDF 归档" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + HANDOFF_ENTRY + h[j + 1:])
        print("  handoff entry added")

    m = io.open(MAP, encoding="utf-8").read()
    row = ("102. 🗄️ **投出版 PDF 归档（2026-10-19 12:45）** —— 新建 `SUBMISSION/_frozen_submitted/`：A1 PAA / Paper A NEUCOM / "
           "P3 R1 共 **12 个投出版 PDF** + `SHA256SUMS.txt`（0 mismatch）；本地工作稿已含周检补引（A1 59 页、Paper A 70/50、P3 10），"
           "投稿包一字未动；`SUBMISSION/` 按发布边界不入 git。\n")
    if "投出版 PDF 归档（2026-10-19 12:45）" not in m:
        anchor = "101. 📎 **周检引用补录（2026-10-19 12:40）**"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")

    r = io.open(SUBREADME, encoding="utf-8").read()
    pairs = [
        ("| `PaperA_Neurocomputing/` | **Paper A**（P1+P2 合并）| Neurocomputing（SCIE）| **待投** | ✅ 就绪：**70 页**，审计 `paperA_nc` **READY/A** |",
         "| `PaperA_Neurocomputing/` | **Paper A**（P1+P2 合并）| Neurocomputing（SCIE）| **`NEUCOM-D-26-23760`** | ✅ **已投 2026-10-18**（Submitted）；包 **70 页**，审计 `paperA_nc` READY/A |"),
        ("| `A1_PatternAnalysisApplications/` | **A1** | Pattern Analysis and Applications（SCIE）| **待投** | ✅ 就绪：**45 页** + title page，审计 `a1_paa` **READY/A** |",
         "| `A1_PatternAnalysisApplications/` | **A1** | Pattern Analysis and Applications（SCIE）| Submission ID `0a4629f0-0a6d-45d8-b5b1-3681cc4adc8b`（PAA 稿号待邮件）| ✅ **已投 2026-10-18**（Submission received，技术检查中）；**58 页** + title page |"),
    ]
    changed = False
    for old, new in pairs:
        if r.count(old) == 1:
            r = r.replace(old, new, 1)
            changed = True
            print("  README row updated:", old[:38])
    frozen = ("""

## 投出版 PDF 归档（`_frozen_submitted/`，2026-10-19）

| 子目录 | 内容 |
|---|---|
| `_frozen_submitted/A1_PAA/` | A1 投出时的 Manuscript（58 页）、Title Page、Cover Letter、Graphical Abstract |
| `_frozen_submitted/PaperA_NEUCOM/` | Paper A 投出时的 Manuscript（70 页）、Abstract、Cover Letter、Highlights |
| `_frozen_submitted/P3_PRL_R1/` | P3 R1 投出时的 Manuscript、Supplementary、Cover Letter、Highlights |

共 **12 个 PDF**，逐文件哈希记于 `_frozen_submitted/SHA256SUMS.txt`（生成脚本 `tools/_p1328_archive_submitted_pdfs.py`）。
**目的**：本地工作稿 2026-10-19 已补入修回引用（A1 59 页等），重建时不会覆盖投出版；此处保留不可变副本。
""")
    if "_frozen_submitted" not in r.split("冻结纪律")[0]:
        anchor2 = "\n## 冻结纪律"
        idx = r.find(anchor2)
        if idx >= 0:
            r = r[:idx] + frozen + r[idx:]
            changed = True
            print("  README frozen section added")
    if changed:
        io.open(SUBREADME, "w", encoding="utf-8", newline="").write(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
