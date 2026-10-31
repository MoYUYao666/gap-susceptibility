# -*- coding: utf-8 -*-
r"""Point the tooling at SUBMISSION's new layout and rewrite its index.

Moves done by `_p1242_reorganize_submission.py`; this step updates the places that hard-code the old locations:
  * `tools/_p1169_refresh_nc_submission.py`  OUT: paper合/NC_submission -> SUBMISSION/PaperA_Neurocomputing
  * `tools/_p1236_build_paa_package.py`      OUT: paper_a1/PAA_submission -> SUBMISSION/A1_PatternAnalysisApplications
  * audit profiles: paperA_nc, a1_paa, a1_nn package/freeze paths
and rewrites SUBMISSION/README.md as an index of current vs archived packages.

    python tools/_p1243_update_submission_paths.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

README = """# 投稿包索引（`SUBMISSION/`）

> 整理：**2026-10-18**（`tools/_p1242_reorganize_submission.py`，9 项移动全部哈希校验通过）
> 规则：**根目录只放"当前在用"的投稿包；被取代或已拒的包一律进 `_archive/`，永不删除。**
> 每个移动的旧→新路径见 `_archive/MOVED_2026-10-18.tsv`。

## 当前包（根目录）

| 目录 | 稿件 | 期刊（SCI） | 稿号 | 状态 | 主要文件 |
|---|---|---|---|---|---|
| `PaperA_Neurocomputing/` | **Paper A**（P1+P2 合并）| Neurocomputing（SCIE）| **待投** | ✅ 就绪：**70 页**，审计 `paperA_nc` **READY/A** | `Manuscript.pdf`、`Cover Letter.pdf`（3 页，含 P1 被 PR 拒稿披露）、`Highlights.pdf/.txt`、`latex_source.zip`（45 文件）、`PORTAL_TEXT.md` |
| `A1_PatternAnalysisApplications/` | **A1** | Pattern Analysis and Applications（SCIE）| **待投** | ✅ 就绪：**45 页** + title page，审计 `a1_paa` **READY/A** | `Manuscript.pdf`、`Title Page.pdf`（Declarations）、`Cover Letter.pdf`、`latex_source.zip`（14 文件）、`README.md` |
| `P3_PRL_revision/` | **P3** | Pattern Recognition Letters | `PRLETTERS-D-26-02378R1` | 🔄 **在审（冻结）**，R1 截止 2026-11-02 | 10 页主稿 + 6 页补充 + 回复；`CORRECTED_2026-10-15/`、`UPLOAD_2026-10-15/` **不得改动** |
| `A23_JOE/` | **A23** | IEEE Journal of Oceanic Engineering | `26-0663` | 🔄 **在审（冻结）** | 64 页 IEEE 投稿版 + 补充材料 |
| `Review_PRL/` | **PRL Commentary** | Pattern Recognition Letters | `PRLETTERS-D-26-02402` | 🔄 **在审（冻结）** | 7 页 |

## 归档（`_archive/`）

| 目录 | 是什么 | 何时归档 |
|---|---|---|
| `A1_NeuralNetworks_rejected_2026-10-18/` | A1 投 Neural Networks 的完整包（`NEUNET-D-26-09426`，桌面拒稿、未送审）| 2026-10-18 |
| `PaperA_Neurocomputing_2026-10-12_60pp/` | Paper A 的旧 60 页包（被当前 70 页版取代）| 2026-10-18 |
| `_superseded_P3_PRL_revision/` | P3 修订包的旧版本 | 2026-10-17 |
| `_superseded_P3_PRL_submitted_2026-09-26/` | P3 首次投稿版（`PRLETTERS-D-26-02378`）| 2026-10-12 |
| `_old/` | 更早的投稿历史（P1/PR 等）| 2026-10-12 |
| `scripts/` | 原先散落在 `SUBMISSION/` 根的两个辅助脚本 | 2026-10-18 |
| `MOVED_2026-10-18.tsv` | 本轮全部移动的 old→new 映射 | 2026-10-18 |

## 冻结纪律

- `P3_PRL_revision/{CORRECTED_2026-10-15,UPLOAD_2026-10-15}`、`A23_JOE/`、`Review_PRL/`、
  `_archive/A1_NeuralNetworks_rejected_2026-10-18/` 都是**已投出件**，由 `python -m tools.paper_audit freeze --profile …` 守护；
- 任何改动都会触发 P0 审计失败；替换版本须先有明确决定，再更新基线并在 `HANDOFF.md` 记录。
"""

REPL = [
    ("tools/_p1169_refresh_nc_submission.py",
     'OUT = PA / "NC_submission"',
     'OUT = REPO / "SUBMISSION" / "PaperA_Neurocomputing"'),
    ("tools/_p1236_build_paa_package.py",
     'OUT = os.path.join(A1, "PAA_submission")',
     'OUT = os.path.join(REPO, "SUBMISSION", "A1_PatternAnalysisApplications")'),
    ("tools/paper_audit/profiles.py",
     '        package="NC_submission",\n        package_expected=["Manuscript.pdf", "Cover Letter.pdf", "Highlights.pdf",',
     '        package="SUBMISSION/PaperA_Neurocomputing",\n        package_expected=["Manuscript.pdf", "Cover Letter.pdf", "Highlights.pdf",'),
    ("tools/paper_audit/profiles.py",
     '        package="paper_a1/PAA_submission",',
     '        package="SUBMISSION/A1_PatternAnalysisApplications",'),
    ("tools/paper_audit/profiles.py",
     '        freeze_paths=["SUBMISSION/A1_NeuralNetworks"],\n        notes=("Prepared for Pattern Analysis and Applications',
     '        freeze_paths=["SUBMISSION/_archive/A1_NeuralNetworks_rejected_2026-10-18"],\n        notes=("Prepared for Pattern Analysis and Applications'),
    ("tools/paper_audit/profiles.py",
     '        package="SUBMISSION/A1_NeuralNetworks",',
     '        package="SUBMISSION/_archive/A1_NeuralNetworks_rejected_2026-10-18",'),
    ("tools/paper_audit/profiles.py",
     '        freeze_paths=["SUBMISSION/A1_NeuralNetworks"],\n        notes="Under review (NEUNET-D-26-09426)',
     '        freeze_paths=["SUBMISSION/_archive/A1_NeuralNetworks_rejected_2026-10-18"],\n        notes="Desk-rejected 2026-10-18 (NEUNET-D-26-09426)'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    staged = {}
    for rel, old, new in REPL:
        p = os.path.join(REPO, rel)
        t = staged.get(p) or io.open(p, encoding="utf-8").read()
        n = t.count(old)
        print(f"  {rel:<42} {old.splitlines()[0][:52]!r}: {n}")
        assert n == 1, f"{rel}: expected 1, got {n}"
        staged[p] = t.replace(old, new, 1)
    if not a.apply:
        print("  (dry run)")
        return 0
    for p, t in staged.items():
        io.open(p, "w", encoding="utf-8", newline="").write(t)
        print("  updated", os.path.relpath(p, REPO))
    io.open(os.path.join(REPO, "SUBMISSION", "README.md"), "w", encoding="utf-8", newline="").write(README)
    print("  rewrote SUBMISSION/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
