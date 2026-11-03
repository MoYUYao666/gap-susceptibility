"""Apply the six document fixes that independent audit C raised (2026-10-25).

All of them are append-and-annotate, Chinese (operator-facing), and checkable:

  1. 文件地图.md - the "release" row still says "third commit, not pushed / not tagged"; annotate it as
     superseded and state the final state once (main e66094c + DOI backfill, tag v2.5 unmoved,
     GitHub Release Latest, Zenodo DOI 10.5281/zenodo.23632347).
  2. 文件地图.md - two stale Paper A page counts (67/49 and 68/49) -> annotate with the current 79/56,
     verified from `paper合/main_nc.log` / `main_springer.log` and `tools/_p1454_final_verify.py`.
  3. docs/VENUE_SCI_REGISTRY.md - the five-venue table lacks the 来源URL / 核实日期 columns that the SCI
     rule requires. Add them with an honest `待核` (no invented URL or date) and add the line that the
     MJL re-verification is required before the next submission or resubmission.
  4. docs/tool_number_index_2026-10-25.md - new file mapping each colliding tool number (_p1645 ..
     _p1652) to its two full filenames and to the one actually used this round.
  5. "see also" indexes at the top of the newest file in two parallel-document groups (the A23 chain and
     the v2.5 readiness pair).
  6. 文件地图.md - supplement size 433931 -> 434348 bytes (pages/tables/sections 26/50/46 are correct),
     and the POPE headline now leads with the pre-declared verdict instead of the phrase
     "指标依赖结果" (numbers unchanged).

Verification used for the counts:
  `paper3/paper_ieee/supplementary/supplementary.log` -> "Output written on supplementary.pdf
  (26 pages, 434348 bytes)"; `python tools/_p1454_final_verify.py --apply` -> pages
  {a1 64, main_nc 79, main_springer 56, P3 10, A23 73, commentary 7} pass: True.

Idempotent: every edit is skipped when its new text is already present.

Usage:
    python tools/_p1660_audit_doc_fixes.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EDITS = []


def edit(rel, old, new, why):
    EDITS.append((rel, old, new, why))


# ---------------------------------------------------------------- 1. release status row (文件地图)
edit("文件地图.md",
     "> | **发布** | `publish_clean` 第三提交已建（基线 `5ad7724`），**未 push / 未 tag** | "
     "`git -C publish_clean log --oneline -1` |",
     "> | **发布** | ~~`publish_clean` 第三提交已建（基线 `5ad7724`），**未 push / 未 tag**~~ → "
     "**⛔ 已过期（2026-10-25 11:13–11:37）**，终态只在此处写一次：`main` = **`e66094c`**"
     "（DOI 回填后为 **`b743651`**）；tag **`v2.5`**（注解对象 `03e6cebf…`，**未移动**）；"
     "**GitHub Release 已建并标 `Latest`**；**Zenodo v2.5 版本 DOI `10.5281/zenodo.23632347`** 已发布并回填 "
     "| `git -C publish_clean ls-remote --tags ssh-origin`；`gh release list`；"
     "`git -C publish_clean log --oneline -2` |",
     "release row: annotate as superseded, state the final state once")

# ---------------------------------------------------------------- 2a. Paper A page counts (目录表)
edit("文件地图.md",
     "| `paper合/` | **Paper A 主稿**（`sections/` 源、`main_nc.pdf` 67 页、`main_springer.pdf` 49 页、"
     "`NC_submission/` 投稿包）| 稿件树，按路径被文档引用 |",
     "| `paper合/` | **Paper A 主稿**（`sections/` 源、`main_nc.pdf` ~~67~~ **79** 页、"
     "`main_springer.pdf` ~~49~~ **56** 页、`NC_submission/` 投稿包）| 稿件树，按路径被文档引用；"
     "**页数 2026-10-25 复核更正（原 67/49 已过期）**，来源 `paper合/main_nc.log` 与 "
     "`paper合/main_springer.log` 的 \"Output written\"，与 `tools/_p1454_final_verify.py` 的 PAGES 一致 |",
     "paper合 row: 67/49 -> 79/56 with superseded annotation")

# ---------------------------------------------------------------- 2b. Paper A page counts (10-17 block)
edit("文件地图.md",
     "> | **Paper A** | **可投**：NC **68 页** / Springer **49 页**；",
     "> | **Paper A** | **可投**：NC ~~68~~ **79 页** / Springer ~~49~~ **56 页**"
     "（**页数 2026-10-25 复核更正，原 68/49 已过期**）；",
     "10-17 status block: 68/49 -> 79/56 with superseded annotation")

# ---------------------------------------------------------------- 6a. supplement byte size
edit("文件地图.md", "433931 bytes", "434348 bytes",
     "supplement size 433931 -> 434348 B (pages/tables/sections unchanged: 26/50/46)")

# ---------------------------------------------------------------- 6b. POPE headline wording
edit("文件地图.md",
     "> | **POPE 第二下游** | 已整合为**指标依赖**结果：accuracy 与 token F1 升、yes-class F1 降；",
     "> | **POPE 第二下游** | 已整合为第二下游结果，**以预声明判定为首**："
     "`claim_verdict.second_task_verdict = supports_the_adapters`（该判定**仅就 accuracy** 而言）；"
     "同时如实记录**指标方向**——accuracy 与 token F1 升、**yes-class F1 降**；",
     "POPE headline: lead with the pre-declared verdict, keep the metric directions (no number changed)")

# ---------------------------------------------------------------- 3. VENUE SCI registry
edit("docs/VENUE_SCI_REGISTRY.md",
     "| 稿件 | 刊名 | ISSN | 出版商 | 收录 | 稿号 | 核实状态 |\n"
     "|---|---|---|---|---|---|---|\n"
     "| Paper A（`paper合/`）| Neurocomputing | 0925-2312 | Elsevier | SCIE | "
     "`NEUCOM-D-26-23760`（With Editor）| 已投事实；下次投稿前按 §2 复核 |\n"
     "| A1（`paper_a1/`）| Pattern Analysis and Applications | 1433-7541 | Springer | SCIE | "
     "`0a4629f0-…`（With editor）| 同上 |\n"
     "| P3（`paper3/paper_ieee/`）| Pattern Recognition Letters | 0167-8655 | Elsevier | SCIE | "
     "`PRLETTERS-D-26-02671`（With Editor）| 同上 |\n"
     "| A23（`paper_a2/`）| IEEE Journal of Oceanic Engineering | 0364-9059 | IEEE | SCIE | "
     "`26-0663` | 同上 |\n"
     "| Commentary（`paper_review_prl/`）| Pattern Recognition Letters | 0167-8655 | Elsevier | "
     "SCIE | `PRLETTERS-D-26-02402`（在审）| 同上 |",
     "| 稿件 | 刊名 | ISSN | 出版商 | 收录 | 稿号 | 核实状态 | 来源URL | 核实日期 |\n"
     "|---|---|---|---|---|---|---|---|---|\n"
     "| Paper A（`paper合/`）| Neurocomputing | 0925-2312 | Elsevier | SCIE | "
     "`NEUCOM-D-26-23760`（With Editor）| 已投事实；下次投稿前按 §2 复核 | 待核 | 待核 |\n"
     "| A1（`paper_a1/`）| Pattern Analysis and Applications | 1433-7541 | Springer | SCIE | "
     "`0a4629f0-…`（With editor）| 同上 | 待核 | 待核 |\n"
     "| P3（`paper3/paper_ieee/`）| Pattern Recognition Letters | 0167-8655 | Elsevier | SCIE | "
     "`PRLETTERS-D-26-02671`（With Editor）| 同上 | 待核 | 待核 |\n"
     "| A23（`paper_a2/`）| IEEE Journal of Oceanic Engineering | 0364-9059 | IEEE | SCIE | "
     "`26-0663` | 同上 | 待核 | 待核 |\n"
     "| Commentary（`paper_review_prl/`）| Pattern Recognition Letters | 0167-8655 | Elsevier | "
     "SCIE | `PRLETTERS-D-26-02402`（在审）| 同上 | 待核 | 待核 |",
     "venue table: add the required 来源URL / 核实日期 columns with an honest 待核")

edit("docs/VENUE_SCI_REGISTRY.md",
     "> 说明：这五条是**已发生的投稿事实**。",
     "> **⚠️ 2026-10-25 独立审计补记**：上表已补 `来源URL` 与 `核实日期` 两列，但**两列目前全部是 `待核`**——\n"
     "> 本轮**没有**对任何一家刊物按 §2 做 MJL 复核，因此**不填 URL、不填日期**（编造比留空更糟）。\n"
     "> **结论：这五篇的下一次投稿或改投之前，必须先按 §2 用 Clarivate Master Journal List 逐条复核，\n"
     "> 把 `来源URL` 与 `核实日期` 补成真实值，并登记核实人；未补齐之前，本表不构成 §2 要求的留痕。**\n"
     "\n"
     "> 说明：这五条是**已发生的投稿事实**。",
     "venue table: add the explicit MJL-reverification-required line")

# ---------------------------------------------------------------- 7. HANDOFF page-count correction
# Source of the counts: paper_a2/main_ieee.log, paper3/.../supplementary.log, the PAGES constant of
# tools/_p1454_final_verify.py, and audit A's report docs/audit_manuscripts_2026-10-25.md (L105, L109,
# L158, L162). The gate scripts themselves are NOT touched (that is task-23).
edit("HANDOFF.md",
     "④ 唯一剩余：A23 下一版修订的 cover letter。",
     "④ 唯一剩余：A23 下一版修订的 cover letter。\n"
     "\n"
     "### 7. 页数更正与冻结件复核（2026-10-25 补记，来自独立审计 A）\n"
     "\n"
     "- **页数口径更正（旧值已过期；不改写历史行，只在此注明终值）**：\n"
     "  - **A23 72 → 73 页**：2026-10-24 19:30 那条写的是 72 页且从未记录这次变更；现值为 **73**，来源\n"
     "    `paper_a2/main_ieee.log` 的 \"Output written on main_ieee.pdf (73 pages, 1275901 bytes)\"、pypdf，\n"
     "    与 `tools/_p1454_final_verify.py` 的 PAGES 常量一致。\n"
     "  - **P3 补充材料 18 → 26 页**（**46 节 / 50 表**）：来源\n"
     "    `paper3/paper_ieee/supplementary/supplementary.log` 的 \"Output written on supplementary.pdf\n"
     "    (26 pages, 434348 bytes)\"，以及 `supplementary.tex` 中 `\\begin{table*?}`=50、`\\section{`=46。\n"
     "  - 其余五个页数本轮复核**与实况一致**：A1 **64**、Paper A `main_nc` **79** / `main_springer` **56**、\n"
     "    P3 main **10**、Commentary **7**（来源 `python tools/_p1454_final_verify.py --apply` 的\n"
     "    `pages: {...} pass: True`）。\n"
     "- **冻结件/提交件复核（审计 A 实测）**：对五个 `tools/paper_audit/freeze/*.json` 清单与三份\n"
     "  `SHA256SUMS.txt` 共 **133 条记录**（107 + 26）逐条重算哈希，**0 处变化**；`SUBMISSION/**` 跑门禁\n"
     "  前后两次清点均为 **558 文件 / 78.3 MiB** ⇒ **本轮未改动任何提交件或冻结件**。\n"
     "  来源 `docs/audit_manuscripts_2026-10-25.md`（L158、L162）。\n"
     "- **七份 PDF 全部从源码重建**：**0 错误 / 0 未定义引用 / 0 未定义引文 / 0 overfull hbox /\n"
     "  0 overfull vbox**，且每个页数都与其常量一致 ⇒ 草稿确实能干净构建。\n"
     "  来源 `docs/audit_manuscripts_2026-10-25.md`（L105、L109）。\n"
     "- **注**：审计 A 的其他发现（白名单 I-02、未使用的 warn 列表、staged-package 快照过期）归 task-23；\n"
     "  `tools/_p1454_final_verify.py` 等门禁脚本**本 agent 未改动**。",
     "HANDOFF: dated page-count correction + frozen-package re-verification record")


def insert_after_title(path: Path, block: str, marker: str, apply: bool) -> str:
    text = io.open(path, encoding="utf-8").read()
    if marker in text:
        return "  [skip] %-46s already present" % path.name
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].startswith("#"):
        return "  [FAIL] %-46s no title line" % path.name
    merged = lines[0] + "\n" + block + "".join(lines[1:])
    if apply:
        io.open(path, "w", encoding="utf-8", newline="\n").write(merged)
        path.read_bytes().decode("utf-8")
    return "  [edit] %-46s see-also index inserted" % path.name


A23_SEE_ALSO = """> **参见（A23 同一轮共 6 份笔记，按时间序）**：`a23_multiencoder_round_notes.md`（2026-10-24 上一轮）→
> `a23_multiencoder_rerun_notes.md`（重跑口径）→ `a23_multiencoder_cloud_notes.md`（云端多编码器）→
> `a23_21unit_switch_notes.md`（21 单元切换）→ `a23_transfer_claim_rewrite_notes.md`（迁移主张改写）→
> **本文件**（下一版修订包，最新）。**冲突时以本文件为准**；更早的 `a23_fine_eps_round_notes.md` 属另一主题（细 ε 证书）。
"""
A23_MARKER = "参见（A23 同一轮共 6 份笔记"

V25_SEE_ALSO = """> **参见**：`docs/V25_READINESS_2026-10-24.md`（v2.5 就绪评估，2026-10-24）与 **本文件**
> （发布准备 + DOI 回填，2026-10-25，最新）。**冲突时以本文件为准**。
"""
V25_MARKER = "参见**：`docs/V25_READINESS_2026-10-24.md`"

TOOL_INDEX = """# 工具编号对照索引（2026-10-25）

> **为什么有这个文件**：本轮并行推进时，不同 agent 各自递增编号，导致 **`_p1645`–`_p1652` 每个编号下各有两个
> 不同名的脚本**（文件名不同，**没有任何文件被覆盖**）。HANDOFF / 笔记里的“`_p1645` 修了归档”这类简称，
> 单看编号会指错文件。本表把每个编号映射到**两个完整文件名**，并标明**本轮实际用的是哪一个**。
> 规则：正文引用时**必须写完整文件名**，不要只写编号；本表只做消歧，**不重命名任何文件**。

| 编号 | 文件 A | 文件 B | 本轮实际使用 | 说明 |
|---|---|---|---|---|
| `_p1645` | `_p1645_repair_run_archive_block_maps.py` | `_p1645_stage_pope_archive.py` | **A** | A = 用 `allocation_stage.module_ranks` 确定性重建 `block_maps`（我）；B = POPE 归档暂存（POPE agent） |
| `_p1646` | `_p1646_p3_arm_replicates.py` | `_p1646_inspect_pope_aggregate.py` | **A** | A = 每臂 2 次复现性研究（我）；B = 查看 POPE 聚合（POPE agent） |
| `_p1647` | `_p1647_assemble_retrieval.py` | `_p1647_pope_corrected_metrics.py` | **A** | A = 实例失联后补齐 6 个缺失取回文件（我）；B = POPE 指标修正（POPE agent） |
| `_p1648` | `_p1648_probe_bootstrap_variants.py` | —（无重号） | 未被本轮主流程使用 | 仅探测脚本 |
| `_p1649` | `_p1649_append_round2_zh.py` | `_p1649_pope_supplement_insert.py` | **A** | A = 向云轮笔记追加中文一节（我）；B = 向 P3 补充材料插入 POPE 小节（p3-stats） |
| `_p1650` | `_p1650_fix_pope_acceptance_bool.py` | `_p1650_diagnose_p1640_metric_bug.py` | **A** | A = 修 `bool(哨兵字符串)==True` 的诚实性缺陷（我）；B = 诊断 `_p1640` 指标 bug（POPE agent） |
| `_p1651` | `_p1651_update_phase_close_docs.py` | `_p1651_check_supp_pages.py` | **A** | A = 追加 HANDOFF/文件地图/POPE 笔记（我）；B = 检查补充材料页数（POPE agent） |
| `_p1652` | `_p1652_backfill_v25_doi.py` | `_p1652_probe_pope_pdf_needles.py` | **A** | A = v2.5 DOI 回填（我）；B = 探测 PDF 文案（POPE agent） |
| `_p1660` | `_p1660_audit_doc_fixes.py` | —（本文件作者） | 是 | 本表第 1–6 项文档修订的执行脚本；**编号 1653–1659 已被其他 agent 占用，故跳到 1660** |

**核验命令**（列出每个编号下的所有文件）：
```powershell
Get-ChildItem tools -Filter "_p16*.py" | Where-Object { $_.Name -match '^_p16(4[5-9]|5[0-9])_' } | Sort-Object Name
```
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rc = 0

    for rel, old, new, why in EDITS:
        path = REPO / rel
        if not path.is_file():
            print("  [FAIL] missing %s" % rel)
            rc = 2
            continue
        text = io.open(path, encoding="utf-8").read()
        if new in text:
            print("  [skip] %-46s already applied" % rel)
            continue
        n = text.count(old)
        if n != 1:
            print("  [FAIL] %-46s expected 1 occurrence, found %d (%s)" % (rel, n, why))
            rc = 2
            continue
        print("  [edit] %-46s %s" % (rel, why))
        if args.apply:
            io.open(path, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))
            io.open(path, encoding="utf-8").read()   # strict decode check

    # 4. tool-number index
    idx = REPO / "docs" / "tool_number_index_2026-10-25.md"
    if idx.is_file():
        print("  [skip] %-46s already present" % idx.name)
    else:
        print("  [edit] %-46s create the tool-number disambiguation index" % idx.name)
        if args.apply:
            io.open(idx, "w", encoding="utf-8", newline="\n").write(TOOL_INDEX)

    # 5. see-also indexes
    print(insert_after_title(REPO / "docs" / "a23_next_revision_package_notes.md",
                             A23_SEE_ALSO, A23_MARKER, args.apply))
    print(insert_after_title(REPO / "docs" / "V25_RELEASE_PREP_2026-10-25.md",
                             V25_SEE_ALSO, V25_MARKER, args.apply))
    return rc


if __name__ == "__main__":
    sys.exit(main())
