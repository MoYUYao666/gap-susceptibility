"""Document the 2026-10-25 retirement of the last three top-level directories (Task A paper trail).

Updates, append-and-annotate only:

  1. `AGENTS.md` and `CLAUDE.md` - item 5 of the audit-scope rule said the three directories stay at the
     top level because gates reference them. A root-anchored re-check showed that was a FALSE POSITIVE
     (all `_archive/` hits were `SUBMISSION/_archive/...`), the three were moved, so the item is
     replaced by the corrected statement while the old text is kept as a dated historical note.
  2. `docs/PATH_MIGRATION_2026-10-25.md` - new "second pass" section with the three moves, their file
     counts, the reference handling per directory, and the frozen-README case; the old
     "Deliberately NOT moved" heading is struck through (it is history now, not guidance).
  3. `文件地图.md` and `HANDOFF.md` - a dated block inserted under the title (newest-first convention).

Idempotent: every edit checks for its marker first.

Usage:
    python tools/_p1662_retire_docs.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ITEM5_OLD = """5. 三个**因路径被门禁引用而留在顶层的例外**（移动会破坏验证，故原地保留、且不参与内容审核）：
   `_archive/`（被 `tools/paper_audit/profiles.py` 与两份 freeze manifest 引用 ⇒ 涉及 133 条冻结哈希）、
   `paper/`（被 `SUBMISSION/_archive/*/README.md` 归档记录引用）、
   `paper_review/`（被 Commentary 的活跃文档引用）；三者的处理意见需操作者决定。"""

ITEM5_NEW = """5. **三个例外已于 2026-10-25 移入 `弃用/`（本条取代下方原条目）。** 先纠正一个**假阳性**：早先的守卫用
   **朴素子串**匹配，把 `SUBMISSION/_archive/...` 误判成对根级 `_archive/` 的引用；改用**根锚定**匹配重查后，
   53 个门禁脚本里对这三个目录的**根级引用为 0** ⇒ 迁移安全：
   - **`_archive/`（251 文件）→ `弃用/08_历史归档/_archive/`**：`tools/paper_audit/profiles.py` 与五份
     `tools/paper_audit/freeze/*.json` 里的 46 处 `_archive/` **全部是 `SUBMISSION/_archive/...`**（冻结路径，
     未动），与本目录无关 ⇒ **无需改任何引用**，133 条冻结哈希不受影响；
   - **`paper/`（111 文件）→ `弃用/06_归档稿件/paper/`**：引用仅为**冻结** `SUBMISSION/_archive/*/README.md`
     的历史叙述（按冻结规则**未修改**，仅在本文件与此处记录）与 `paper3/README_是哪篇.md` 的一句目录清单
     （**已更新**）；
   - **`paper_review/`（30 文件）→ `弃用/06_归档稿件/paper_review/`**：Commentary 活跃文档 5 处引用**已更新**
     （`MANUSCRIPT.md` ×2、`DRAFT_OUTLINE.md` ×1、`FIXES_2026-10-18.md` ×2，另 `docs/commentary_compression_and_table.md` ×1）。
   ⇒ **顶层不再有例外**；`弃用/` 内一切内容仍**不参与**任何审核/门禁/账本。
   <原条目（2026-10-25 早间，已被本条取代，保留供追溯）：三个因路径被门禁引用而留在顶层的例外 ——
   `_archive/`（被 `tools/paper_audit/profiles.py` 与两份 freeze manifest 引用 ⇒ 涉及 133 条冻结哈希）、
   `paper/`（被 `SUBMISSION/_archive/*/README.md` 归档记录引用）、`paper_review/`（被 Commentary 的活跃文档引用）；
   三者的处理意见需操作者决定。>"""

PATH_OLD = "## Deliberately NOT moved (evidence-based, kept in place and excluded from content audits)"
PATH_NEW = """## Second pass (2026-10-25, later the same day): the three exceptions were moved

The first pass kept three directories at the repository root because a guard reported gate references to
them. That guard matched **naive substrings**, so its `_archive/` hits were all `SUBMISSION/_archive/...`
(a different, frozen path) - a **false positive**. A **root-anchored** re-check over 15,111 text files
found **zero** root-level references to any of the three inside the 53-script gate chain
(`tools/paper_audit/**`, `_p1428`, `_p1637`, `_p1454`, `audit_check.py`, `audit_pdf.py`,
`verify_a23_fix.py`, `_p1181`, `_final_check_prl`, `_claim_ledger*`). They were therefore moved:

| directory | files | new location | reference handling |
|---|---|---|---|
| `_archive/` | 251 | `弃用/08_历史归档/_archive/` | **none needed**: the 46 `_archive/` occurrences in `tools/paper_audit/profiles.py` and the five `tools/paper_audit/freeze/*.json` manifests are all `SUBMISSION/_archive/...` (frozen, untouched) => the 133 frozen hashes are unaffected |
| `paper/` | 111 | `弃用/06_归档稿件/paper/` | live prose in `paper3/README_是哪篇.md` updated; the prose in the **frozen** `SUBMISSION/_archive/PaperA_Neurocomputing_2026-10-12_60pp/README.md` and `SUBMISSION/_archive/_old/P1_PatternRecognition/README.md` was **left untouched** (freeze rule) and stands as a historical record of where the directory was |
| `paper_review/` | 30 | `弃用/06_归档稿件/paper_review/` | 5 live references updated: `paper_review_prl/MANUSCRIPT.md:3,4`, `DRAFT_OUTLINE.md:16`, `FIXES_2026-10-18.md:96,111`; plus `docs/commentary_compression_and_table.md` |

Every move was verified by comparing a `{relative path: (size, sha256)}` inventory before and after: all
three inventories were **identical**, and no source directory remained. Executed by
`tools/_p1661_retire_three_dirs.py` (idempotent, with the same assertions).

`弃用/` now holds **1,005 files** (613 from the first pass + 392 from this one).

## ~~Deliberately NOT moved~~ (first pass, superseded by the section above)"""

MAP_BLOCK = """> **🗂️ 2026-10-25 12:05 状态更新：最后三个顶层例外已移入 `弃用/`；五篇活稿 DOI 升到 v2.5**
>
> | 项 | 结果 | 依据 |
> |---|---|---|
> | `_archive/`（251 文件） | → **`弃用/08_历史归档/_archive/`** | 根锚定复检：门禁链 53 脚本**零根级引用**；`profiles.py`/freeze 清单里的 46 处全是 `SUBMISSION/_archive/...` ⇒ 假阳性已纠正、**无需改引用** |
> | `paper/`（111 文件） | → **`弃用/06_归档稿件/paper/`** | 活引用仅 `paper3/README_是哪篇.md`（已更新）；**冻结** `SUBMISSION/_archive/*/README.md` 的叙述按冻结规则**未动** |
> | `paper_review/`（30 文件） | → **`弃用/06_归档稿件/paper_review/`** | Commentary 活文档 5 处引用**已更新** |
> | 顶层例外 | **已清零** | `AGENTS.md`/`CLAUDE.md` 审核范围规则第 5 条已改写（旧条目保留供追溯） |
> | 活稿 DOI | **五篇统一到 v2.5 `10.5281/zenodo.23632347`** | 见 `docs/retire_exceptions_and_doi_v25_2026-10-25.md` |
> | 迁移脚本 | `tools/_p1661_retire_three_dirs.py`（幂等、带断言） | 移动前后 `{路径:(大小,sha256)}` 清单**逐条相同** |
>
> **注意（提交件 vs 活稿的刻意分歧）**：P3 的**已投冻结包**仍写 v2.2（`10.5281/zenodo.23523263`），
> 活稿现写 **v2.5**——这是"已投件保持原样、活稿跟随最新归档"的**有意**状态，详见
> `docs/P3_SUBMISSION_STATUS.md` 与上述交付件。

"""

HANDOFF_BLOCK = """## 🗂️ 2026-10-25 12:05 —— 归档收尾：三个顶层例外移入 `弃用/`，五篇活稿 DOI 升到 v2.5

**做了什么 → 结果 → 还差什么**

### 1. 迁移：最后三个顶层例外清零

- **先纠假阳性**：早先守卫用朴素子串，把 `SUBMISSION/_archive/...` 误判为根级 `_archive/` 的引用。
  **根锚定**重查 15,111 个文本文件、门禁链 53 个脚本 ⇒ 三个目录的**根级引用为 0**。
- **`_archive/`（251 文件）→ `弃用/08_历史归档/_archive/`**：`tools/paper_audit/profiles.py` 与五份
  `tools/paper_audit/freeze/*.json` 里的 46 处 `_archive/` **全是 `SUBMISSION/_archive/...`**（冻结、未动）
  ⇒ **无需改引用**，**133 条冻结哈希不受影响**。
- **`paper/`（111 文件）→ `弃用/06_归档稿件/paper/`**：活引用仅 `paper3/README_是哪篇.md`（已更新）；
  **冻结** `SUBMISSION/_archive/*/README.md` 的叙述按冻结规则**未修改**，作为"当时此处"的历史记录。
- **`paper_review/`（30 文件）→ `弃用/06_归档稿件/paper_review/`**：Commentary 活文档 5 处引用已更新
  （`MANUSCRIPT.md:3,4`、`DRAFT_OUTLINE.md:16`、`FIXES_2026-10-18.md:96,111`）+ `docs/commentary_compression_and_table.md` ×1。
- **校验**：三次移动前后各做 `{相对路径:(大小,sha256)}` 清单，**逐条相同**、源目录不残留；
  脚本 `tools/_p1661_retire_three_dirs.py`（幂等、带断言）。
- `弃用/` 现 **1,005 文件**（首轮 613 + 本轮 392）。**顶层不再有例外**，`弃用/` 内一切仍不参与审核。

### 2. 活稿 DOI 统一到 v2.5

- 五篇活稿的仓库版本 DOI 由 v2.3（`23609295`）/ v2.2（P3，`23523263`）统一改为
  **v2.5 `10.5281/zenodo.23632347`**，版本标签同步为 "v2.5, 25 October 2026"；逐条 file:line 见
  `docs/retire_exceptions_and_doi_v25_2026-10-25.md`。
- **重编译**六份 PDF，**页数全部保持**：A1 **64**、Paper A NC **79** / Springer **56**、P3 main **10**、
  A23 **73**、Commentary **7**；补充材料 **26 页**。
- **⚠️ 刻意分歧（必须记住）**：**P3 已投冻结包仍写 v2.2**（投稿时的 DOI，冻结规则不许改），
  活稿现写 v2.5 ⇒ **提交件与活稿在 DOI 上不一致是刻意的**，见 `docs/P3_SUBMISSION_STATUS.md`。
- 门禁链里固定旧 DOI 的"针"（`paper3/paper_ieee/audit_check.py`、`audit_pdf.py`、`tools/paper_audit/`、
  台账）已同步更新，避免门禁继续检查过期值。

**待办**：① 无（本轮收尾）；② 下次投稿/改投前仍需按 `docs/VENUE_SCI_REGISTRY.md` 做 MJL 复核；
③ 发布侧无需变更（`publish_clean` 不含稿件，本轮未 push）。

"""


def edit_file(rel: str, old: str, new: str, apply: bool, marker: str | None = None) -> str:
    p = REPO / rel
    if not p.is_file():
        return "  [FAIL] missing %s" % rel
    text = io.open(p, encoding="utf-8").read()
    mk = marker if marker is not None else new
    if mk in text:
        return "  [skip] %-46s already updated" % rel
    n = text.count(old)
    if n != 1:
        return "  [FAIL] %-46s expected 1 occurrence, found %d" % (rel, n)
    if apply:
        io.open(p, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))
        io.open(p, encoding="utf-8").read()
    return "  [edit] %-46s ok" % rel


def insert_after_title(rel: str, block: str, marker: str, apply: bool) -> str:
    p = REPO / rel
    if not p.is_file():
        return "  [FAIL] missing %s" % rel
    text = io.open(p, encoding="utf-8").read()
    if marker in text:
        return "  [skip] %-46s already present" % rel
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].startswith("#"):
        return "  [FAIL] %-46s no title line" % rel
    merged = lines[0] + "\n" + block + "".join(lines[1:])
    if apply:
        io.open(p, "w", encoding="utf-8", newline="\n").write(merged)
        io.open(p, encoding="utf-8").read()
    return "  [edit] %-46s block inserted" % rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    print("== rule files (item 5) ==")
    print(edit_file("AGENTS.md", ITEM5_OLD, ITEM5_NEW, args.apply))
    print(edit_file("CLAUDE.md", ITEM5_OLD, ITEM5_NEW, args.apply))
    print("== migration doc ==")
    print(edit_file("docs/PATH_MIGRATION_2026-10-25.md", PATH_OLD, PATH_NEW, args.apply))
    print("== dated blocks (newest-first) ==")
    print(insert_after_title("文件地图.md", MAP_BLOCK, "2026-10-25 12:05 状态更新", args.apply))
    print(insert_after_title("HANDOFF.md", HANDOFF_BLOCK, "2026-10-25 12:05 —— 归档收尾", args.apply))
    return 0


if __name__ == "__main__":
    sys.exit(main())
