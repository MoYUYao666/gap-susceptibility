"""Backfill the published v2.5 version DOI (10.5281/zenodo.23632347) into the working documents.

Zenodo minted `10.5281/zenodo.23632347` for the `v2.5` GitHub Release (tag `v2.5` -> `e66094c`,
not moved). Everything written before the DOI existed says "no DOI yet" or quotes the previous
version DOI `10.5281/zenodo.23614290` (v2.4). This script updates exactly the working-draft
locations and nothing else:

  1. publish_clean/README.md            - badge + "Latest version DOI" paragraph
  2. publish_clean/RELEASE_NOTES_v2.5.md - tag/DOI status, plus the two "not yet executed" claims
                                          about _p1639/_p1640 which the 2026-10-25 round falsified,
                                          and the four new result archives
  3. docs/V25_RELEASE_PREP_2026-10-25.md - the pre-tag plan text, annotated with the minted DOI
  4. HANDOFF.md                         - the 2026-10-25 "release status" block
  5. docs/P3_SUBMISSION_STATUS.md       - repository DOI version list (English)
  6. 文件地图.md                         - the 2026-10-25 "what remains" block

Deliberately NOT changed (and why):

  * `SUBMISSION/**` - frozen submitted packages keep the DOI they were submitted with.
  * any manuscript .tex - none of the five quotes `23614290`. They quote `23609295` (v2.3); P3 quotes
    `23523263` (v2.2) on purpose because that is the DOI of the submitted package
    (`docs/P3_CHANGE_SUMMARY_2026-10-24.md:154`). Bumping a live draft away from its submitted
    state is a decision for the lead, not a DOI backfill; so page counts and PDFs are untouched.
  * `publish_clean/RELEASE_NOTES_v2.4.md` - historical record of v2.4's own DOI.
  * `tools/_p1625_p3_consistency_fixes.py`, `tools/_p1626_fix_status_doi_block.py` - one-shot 10-24
    revision scripts (repository rule: historical scripts stay byte-frozen). Their old-text
    assertions are therefore stale; that is recorded in the report, not "fixed" by editing history.
  * `docs/*round_notes*.md` and the dated 2026-10-24 entries - historical statements true at the time.

Idempotent: each edit checks for its new text first.

Usage:
    python tools/_p1652_backfill_v25_doi.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OLD = "10.5281/zenodo.23614290"
NEW = "10.5281/zenodo.23632347"
CONCEPT = "10.5281/zenodo.23341082"

EDITS = []


def edit(rel_path: str, old: str, new: str, why: str) -> None:
    EDITS.append((rel_path, old, new, why))


# ---------------------------------------------------------------- 1. publish_clean/README.md
edit("publish_clean/README.md",
     "[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23614290.svg)]"
     "(https://doi.org/10.5281/zenodo.23614290)",
     "[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23632347.svg)]"
     "(https://doi.org/10.5281/zenodo.23632347)",
     "README badge -> v2.5 version DOI")

edit("publish_clean/README.md",
     "**Latest version DOI: [10.5281/zenodo.23614290](https://doi.org/10.5281/zenodo.23614290)** — "
     "this resolves to the\n`v2.4` release and is the persistent identifier to cite for the current "
     "code and results. Earlier snapshots remain\navailable under "
     "[10.5281/zenodo.23609295](https://doi.org/10.5281/zenodo.23609295) (`v2.3`) and\n"
     "[10.5281/zenodo.23341223](https://doi.org/10.5281/zenodo.23341223) (`v1.0-prl-revision`).",
     "**Latest version DOI: [10.5281/zenodo.23632347](https://doi.org/10.5281/zenodo.23632347)** — "
     "this resolves to the\n`v2.5` release and is the persistent identifier to cite for the current "
     "code and results. Earlier snapshots remain\navailable under "
     "[10.5281/zenodo.23614290](https://doi.org/10.5281/zenodo.23614290) (`v2.4`),\n"
     "[10.5281/zenodo.23609295](https://doi.org/10.5281/zenodo.23609295) (`v2.3`) and\n"
     "[10.5281/zenodo.23341223](https://doi.org/10.5281/zenodo.23341223) (`v1.0-prl-revision`).",
     "README latest-version paragraph -> v2.5, v2.4 demoted to 'earlier'")

# ------------------------------------------------- 2. publish_clean/RELEASE_NOTES_v2.5.md
edit("publish_clean/RELEASE_NOTES_v2.5.md",
     "**Not yet tagged.** These files are on `main` and form the next version; no version DOI has "
     "been\nminted, because a Zenodo version DOI is created by the `v2.5` tag.",
     "**Tagged and archived.** The `v2.5` tag points at `e66094c` and the matching GitHub Release is\n"
     "published (marked `Latest`), so Zenodo minted **Version DOI: `10.5281/zenodo.23632347`**\n"
     "(concept DOI `10.5281/zenodo.23341082`). The tag was not moved: the DOI backfill for this\n"
     "release is a metadata-only change and does not warrant a new tag or a new DOI.",
     "release notes: 'not yet tagged / no DOI' -> tagged + v2.5 DOI")

edit("publish_clean/RELEASE_NOTES_v2.5.md",
     "  - `_p1639_p3_official_igu.py` - runs the **official** IGU-LoRA allocator under the "
     "block-level\n    comparison protocol and quantifies the gap to our block-level reimplementation. "
     "**Written but\n    not yet executed: it needs the cloud instance;**",
     "  - `_p1639_p3_official_igu.py` - runs the **official** IGU-LoRA allocator under the "
     "block-level\n    comparison protocol and quantifies the gap to our block-level reimplementation. "
     "**Executed on\n    the 2026-10-25 cloud round** (six arms: two allocations x three seeds). "
     "The pre-declared\n    verdict is `small`: paired mean gap -59.5, 95% CI [-150.5, -8.0], margin "
     "196.05, block-level\n    L1 = 2 of 16;",
     "release notes: _p1639 'not yet executed' -> executed with the pre-declared verdict")

edit("publish_clean/RELEASE_NOTES_v2.5.md",
     "  - `_p1640_p3_second_downstream.py` - a **second** downstream task, POPE (object "
     "hallucination),\n    evaluated with the exact conventions of the VQA-RAD check so the two are "
     "comparable. **Written\n    but not yet executed: it needs the cloud instance;**",
     "  - `_p1640_p3_second_downstream.py` - a **second** downstream task, POPE (object "
     "hallucination),\n    evaluated with the exact conventions of the VQA-RAD check so the two are "
     "comparable. **Executed on\n    the 2026-10-25 cloud round**: three arms (base, r5, r6) over "
     "3,000 questions; the\n    metric-dependent outcome is that accuracy and token F1 improve while "
     "the yes-class F1 falls,\n    and the prepared-parquet row order is verified;",
     "release notes: _p1640 'not yet executed' -> executed with the metric-dependent outcome")

edit("publish_clean/RELEASE_NOTES_v2.5.md",
     "  - refreshed claim ledgers and the final verification record.",
     "  - the 2026-10-25 cloud-round archives: `p3_official_igu_run.json` (the six arms),\n"
     "    `p3_official_vs_reimpl.json` (the official-versus-reimplementation verdict),\n"
     "    `p3_official_igu_replicates.json` (three identical runs per arm: spread max 132.0,\n"
     "    mean 76.1 - the same order as the gap being judged) and `p3_second_downstream.json`\n"
     "    (POPE, with the prepared-parquet row-order check verified);\n"
     "  - refreshed claim ledgers and the final verification record.",
     "release notes: list the four cloud-round archives that are actually in this release")

# ------------------------------------------- 3. docs/V25_RELEASE_PREP_2026-10-25.md
edit("docs/V25_RELEASE_PREP_2026-10-25.md",
     "  **本次刻意未改 README**，因为 tag 之前不存在该 DOI，写了就是编造。",
     "  **本次刻意未改 README**，因为 tag 之前不存在该 DOI，写了就是编造。\n"
     "- **✅ 2026-10-25 回填（本文件的计划已执行完毕）**：Zenodo 已铸出 **v2.5 版本 DOI\n"
     f"  `{NEW}`**（concept DOI `{CONCEPT}`）；GitHub Release `v2.5` 已建并标为 `Latest`，\n"
     "  tag `v2.5` **未移动**（仍指 `e66094c`）。`publish_clean/README.md` 的徽章与 “Latest version DOI”\n"
     f"  已由 `{OLD}`（v2.4）改为 `{NEW}`（v2.5），v2.4/v2.3/v1.0 仍在 “Earlier snapshots” 列出；\n"
     "  `publish_clean/RELEASE_NOTES_v2.5.md` 的 “尚未打 tag / 无版本 DOI”与 `_p1639`/`_p1640`\n"
     "  “尚未执行”三处陈述已按事实改写。核验见 `docs/audit_release_cloud_2026-10-25.md` §1.4–§1.5。",
     "prep doc: record that the plan was executed and the DOI landed")

edit("docs/V25_RELEASE_PREP_2026-10-25.md",
     "- **`_p1639` 官方实现对比与 `_p1640` POPE 第二下游任务：已写好但尚未执行，需要云实例**（两者的产物\n"
     "  `p3_official_igu_run.json` / `p3_official_vs_reimpl.json` / `p3_second_downstream.json` 实测均不存在，\n"
     "  故只能发布脚本、不能发布结果）；",
     "- ~~**`_p1639` 官方实现对比与 `_p1640` POPE 第二下游任务：已写好但尚未执行，需要云实例**~~ →\n"
     "  **✅ 已过期（2026-10-25）**：两者都在 2026-10-25 云端轮执行完毕，产物已取回并入库：\n"
     "  `p3_official_igu_run.json`（六臂）、`p3_official_vs_reimpl.json`（判定 `small`）、\n"
     "  `p3_official_igu_replicates.json`（复现性 132.0/76.1）、`p3_second_downstream.json`（POPE）；\n"
     "  故本轮**可以也应当发布结果**，`RELEASE_NOTES_v2.5.md` 已同步改写；",
     "prep doc: mark the 'not executed' claim as superseded by the executed round")

# ---------------------------------------------------------------- 4. HANDOFF.md
edit("HANDOFF.md",
     "- `publish_clean` 现为 **`5ad7724`**（v2.5 两提交之上再叠加本轮第三提交，见下）。\n"
     "  本轮把云轮归档、修正后的 POPE 聚合、新工具、以及 notes 之外的发布件同步进去；\n"
     "  **未 push、未 tag**。推送与 `v2.5` tag、Zenodo DOI 由 lead 执行。\n"
     "- **边界**：不含稿件、不含权重、无 ≥100 MB 文件；`docs/**` 按操作者指示不入公开仓库。\n"
     "\n"
     "**待办**：① lead 执行 push `main` + tag `v2.5` + 取 Zenodo DOI；② `HANDOFF.md` 的\n"
     "`tools/` 行号引用本轮未受影响（新脚本一律新增，不改旧文件）；③ 云端侧**已无待办**\n"
     "（实例已停、产物已取回、验收已闭环）。",
     "- ~~`publish_clean` 现为 `5ad7724`；本轮把云轮归档、修正后的 POPE 聚合、新工具同步进去，\n"
     "  **未 push、未 tag**~~ → **✅ 已过期（2026-10-25 11:13–11:20）**：\n"
     "  - `main` 已推到 **`e66094c`**（= 我的第三提交 `9976333` + lead 的收尾提交）；\n"
     "  - **tag `v2.5`**（annotated，`03e6cebf…`）指向 `e66094c`，**未移动**；v1.0-prl-revision 与 v2.0–v2.4\n"
     "    的注解对象哈希与远端逐一相同（独立审计 `docs/audit_release_cloud_2026-10-25.md` §1）；\n"
     "  - **GitHub Release `v2.5`** 已建且标 `Latest`（`gh release list`）；\n"
     f"  - **Zenodo v2.5 版本 DOI `{NEW}`**（concept `{CONCEPT}`，Release 摄取生效）；\n"
     "  - 该 DOI 已回填 `publish_clean/README.md`（徽章 + Latest version DOI）与\n"
     "    `RELEASE_NOTES_v2.5.md`；**未新增 tag、未重建 Release**（README/元数据改动不铸新 DOI）。\n"
     "- **边界**：不含稿件、不含权重、无 ≥100 MB 文件；`docs/**` 按操作者指示不入公开仓库。\n"
     "\n"
     "**待办**：① ~~push + tag + Zenodo DOI~~ **已完成**；② `HANDOFF.md` 的 `tools/` 行号引用本轮\n"
     "未受影响（新脚本一律新增，不改旧文件）；③ 云端侧**已无待办**（实例已停、产物已取回、验收已闭环）；\n"
     "④ 唯一剩余：A23 下一版修订的 cover letter。",
     "HANDOFF 2026-10-25: release status -> pushed, tagged, Release, DOI, backfilled")

# ------------------------------------------------- 5. docs/P3_SUBMISSION_STATUS.md
edit("docs/P3_SUBMISSION_STATUS.md",
     "## Repository DOI versions (2026-10-24)\n"
     "\n"
     f"- `v2.4` (current repository release, 2026-10-24): **{OLD}**.\n"
     "- `v2.2` (DOI cited by the submitted manuscript PRLETTERS-D-26-02671): 10.5281/zenodo.23523263; kept frozen.\n"
     "- `v2.3` (superseded release, recorded 2026-10-24): 10.5281/zenodo.23609295; kept frozen.\n"
     "- `v1.0-prl-revision` (historical): 10.5281/zenodo.23341223.",
     "## Repository DOI versions (2026-10-25)\n"
     "\n"
     f"- `v2.5` (current repository release, 2026-10-25): **{NEW}** (concept DOI `{CONCEPT}`).\n"
     f"- `v2.4` (superseded release, 2026-10-24): {OLD}.\n"
     "- `v2.2` (DOI cited by the submitted manuscript PRLETTERS-D-26-02671): 10.5281/zenodo.23523263; kept frozen.\n"
     "- `v2.3` (superseded release, recorded 2026-10-24): 10.5281/zenodo.23609295; kept frozen.\n"
     "- `v1.0-prl-revision` (historical): 10.5281/zenodo.23341223.",
     "P3 status doc: add v2.5 as current, demote v2.4 (v2.2 stays the submitted manuscript's DOI)")

# ---------------------------------------------------------------- 6. 文件地图.md
edit("文件地图.md",
     "> **还剩什么（仅两件，均在 lead 手上）**：\n"
     "> ① **v2.5 的 push + tag + Zenodo DOI**（按 DOI/tag 冻结纪律：新版本用新 tag，**不得**重打已冻结的 tag）；\n"
     "> ② **A23 下一版修订的 cover letter**。",
     "> **还剩什么**：\n"
     "> ① ~~v2.5 的 push + tag + Zenodo DOI~~ → **✅ 已完成（2026-10-25）**：`main`=`e66094c`；\n"
     ">    tag `v2.5`（注解对象 `03e6cebf…`，**未移动**）；GitHub Release 标 `Latest`；\n"
     f">    **Zenodo v2.5 版本 DOI `{NEW}`**（concept `{CONCEPT}`）；已回填 `publish_clean/README.md` 与\n"
     ">    `RELEASE_NOTES_v2.5.md`（审计：`docs/audit_release_cloud_2026-10-25.md` §1.4–§1.5）；\n"
     "> ② **A23 下一版修订的 cover letter**（现在唯一剩余）。",
     "文件地图: mark push/tag/DOI as done with the version DOI")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rc = 0
    touched = {}
    for rel, old, new, why in EDITS:
        path = REPO / rel
        if not path.is_file():
            print("ERROR: missing %s" % rel)
            rc = 2
            continue
        text = io.open(path, encoding="utf-8").read()
        if new in text:
            print("  [skip] %-46s already applied (%s)" % (rel, why))
            continue
        n = text.count(old)
        if n != 1:
            print("  [FAIL] %-46s expected 1 occurrence, found %d (%s)" % (rel, n, why))
            rc = 2
            continue
        print("  [edit] %-46s %s" % (rel, why))
        if args.apply:
            merged = text.replace(old, new, 1)
            io.open(path, "w", encoding="utf-8", newline="\n").write(merged)
            check = io.open(path, encoding="utf-8").read()
            assert new in check, "replacement did not take in %s" % rel
            path.read_bytes().decode("utf-8")       # strict decode: no mixed encoding
            touched[rel] = len(merged.splitlines())

    if args.apply and touched:
        print("\n== files written ==")
        for rel, lines in sorted(touched.items()):
            print("  %-46s %d lines" % (rel, lines))
    if args.apply and rc == 0:
        print("\nold DOI remaining in working documents (must be only frozen/historical places):")
        for rel in ("publish_clean/README.md", "publish_clean/RELEASE_NOTES_v2.5.md",
                    "docs/V25_RELEASE_PREP_2026-10-25.md", "HANDOFF.md",
                    "docs/P3_SUBMISSION_STATUS.md", "文件地图.md"):
            text = io.open(REPO / rel, encoding="utf-8").read()
            print("  %-46s %d occurrence(s) of %s" % (rel, text.count(OLD), OLD))
    return rc


if __name__ == "__main__":
    sys.exit(main())
