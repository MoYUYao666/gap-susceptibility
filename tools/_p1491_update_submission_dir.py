# -*- coding: utf-8 -*-
r"""Update the SUBMISSION directory: archive the rejected P3 package and add the prepared resubmission package.

    python tools/_p1491_update_submission_dir.py [--apply]

Moves SUBMISSION/P3_PRL_revision -> SUBMISSION/_archive/P3_PRL_rejected_2026-10-21 (hash-verified), creates
SUBMISSION/P3_PRL_resubmission from the current build (_venue_builds/P3_PRL_next), writes the decision record and updates
SUBMISSION/README.md.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUB = os.path.join(REPO, "SUBMISSION")
SRC = os.path.join(SUB, "P3_PRL_revision")
DST = os.path.join(SUB, "_archive", "P3_PRL_rejected_2026-10-21")
BUILD = os.path.join(SUB, "_venue_builds", "P3_PRL_next")
RESUB = os.path.join(SUB, "P3_PRL_resubmission")
README = os.path.join(SUB, "README.md")

RESUB_FILES = ["Manuscript.pdf", "Supplementary.pdf", "CoverLetter.pdf", "TitlePage.pdf", "Highlights.pdf",
               "LaTeXSource.zip"]

DECISION = """# P3 decision record

- Manuscript: P3 (`paper3/paper_ieee/`), title "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry:
  Identifiability, Negative Results, and Protocol Dependence" (resubmission title).
- Journal: Pattern Recognition Letters; manuscript number `PRLETTERS-D-26-02378R1`.
- Decision: **Rejected** on 2026-10-21 (Editor-in-Chief Yonghuai Liu). Associate Editor reason (verbatim):
  *"there are some remaining issues regarding the soundness of certain technical choice and interpretation of
  experimental results which haven't been substantially addressed in the current version."*
- Reviewer reports: held on the Editorial Manager peer-review platform; not received by the author.
- This directory preserves the submitted package and the revision-era uploads; it is frozen.
- The prepared new submission is in `SUBMISSION/P3_PRL_resubmission/` (not yet submitted).
"""

RESUB_README = """# P3 resubmission package (prepared, not submitted)

| item | file | note |
|---|---|---|
| Manuscript | `Manuscript.pdf` | 10 pages; new subtitle |
| Supplementary | `Supplementary.pdf` | 8 pages, S1-S17 |
| Cover letter | `CoverLetter.pdf` | 2 pages; discloses prior ID `PRLETTERS-D-26-02378R1` |
| Title page | `TitlePage.pdf` | new title |
| Highlights | `Highlights.pdf` | 5 bullets, <=85 characters |
| LaTeX source | `LaTeXSource.zip` | standalone compile verified |

Status: **prepared only** - the operator submits it through Editorial Manager as a *new submission*.
Prior decision record: `../_archive/P3_PRL_rejected_2026-10-21/DECISION_REJECTED_2026-10-21.md`.
All file names are underscore-free (project rule, 2026-10-21).
"""


def tree_hashes(root: str) -> dict:
    out = {}
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, root)
            h = hashlib.sha256(io.open(p, "rb").read()).hexdigest()
            out[rel] = h
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    changed = False
    if os.path.isdir(SRC) and not os.path.isdir(DST):
        before = tree_hashes(SRC)
        os.makedirs(os.path.dirname(DST), exist_ok=True)
        shutil.move(SRC, DST)
        after = tree_hashes(DST)
        assert before == after, "hash mismatch after move"
        io.open(os.path.join(DST, "DECISION_REJECTED_2026-10-21.md"), "w", encoding="utf-8", newline="").write(DECISION)
        print(f"  archived P3 package ({len(before)} files, hashes verified)")
        changed = True
    if os.path.isdir(BUILD) and not os.path.exists(os.path.join(RESUB, "Manuscript.pdf")):
        os.makedirs(RESUB, exist_ok=True)
        for f in RESUB_FILES:
            src = os.path.join(BUILD, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(RESUB, f))
        io.open(os.path.join(RESUB, "README.md"), "w", encoding="utf-8", newline="").write(RESUB_README)
        print("  created P3_PRL_resubmission package")
        changed = True
    # README index
    r = io.open(README, encoding="utf-8").read()
    old_row = ("| `P3_PRL_revision/` | **P3** | Pattern Recognition Letters | `PRLETTERS-D-26-02378R1` | "
               "🔄 **在审（冻结）**，R1 截止 2026-11-02 | 10 页主稿 + 6 页补充 + 回复；`CORRECTED_2026-10-15/`、"
               "`UPLOAD_2026-10-15/` **不得改动** |")
    new_rows = ("| `P3_PRL_resubmission/` | **P3（改投稿）** | Pattern Recognition Letters（新投稿）| 待提交 | "
                "📝 **已备好、未提交**（2026-10-21）| 10 页主稿 + 8 页补充 + CoverLetter/TitlePage/Highlights/LaTeXSource"
                "（文件名均无下划线）|\n"
                "| `_archive/P3_PRL_rejected_2026-10-21/` | **P3 被拒版本** | Pattern Recognition Letters | "
                "`PRLETTERS-D-26-02378R1` | ❌ **Rejected 2026-10-21**（已归档，冻结）| 原 10+6 页包 + 历次上传 + 决定记录 |")
    if old_row in r and "P3_PRL_resubmission/" not in r:
        r = r.replace(old_row, new_rows, 1)
        changed = True
        print("  SUBMISSION/README.md index updated")
    if "P3_PRL_resubmission" in r and "本地升级构建" not in r:
        r = r.rstrip() + """

## 本地升级 / 修回构建（`_venue_builds/`，2026-10-21）

| 目录 | 内容 | 页数 |
|---|---|---|
| `A1_PAA_next/` | A1 本地升级版（provenance 附录、monitoring 扩展）| 64 |
| `PaperA_Neurocomputing_next/` | Paper A 本地升级版（provenance、ODE 诊断附录）| 74 |
| `P3_PRL_next/` | P3 改投构建（正文 + 8 页补充 + 新封面信）| 10 |
| `A23_JOE_next/` | A23 本地升级版（probes、校准附录）| 70 |
| `Commentary_PRL_next/` | Commentary（2026 引用 + acceptance tests）| 7 |

所有包内投稿文件名均不含下划线；staged 独立编译 1:1 通过。
"""
        changed = True
        print("  build section added to README")
    if changed:
        io.open(README, "w", encoding="utf-8", newline="").write(r)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
