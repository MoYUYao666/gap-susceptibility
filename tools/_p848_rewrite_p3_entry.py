# -*- coding: utf-8 -*-
r"""Insert the P3 "With Editor" entry into HANDOFF.md and 文件地图.md, escape-safe.

Replaces tools/_p846_record_p3_editor.py, which lost backslashes when it was authored: the literal
text `\title{...}` inside its entry string arrived as a real TAB, so the two documents gained
`	itle{...}`. Two guards here make that class of bug impossible:

* every backslash is built from chr(92) instead of an escape sequence in a string literal;
* the finished entry is asserted to contain the exact literal `\title{...}` and to contain no TAB
  character at all before either file is written.

The same collapse already damaged 文件地图.md lines 38/40/42/790/798/805 long before this session
(`	estzip`, `	ools/`, `\x08ackups/`). Those are left alone: the scope ruling is "只管今后，存量不动".

    python tools/_p848_rewrite_p3_entry.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
TEX = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / "latex_source" / "main.tex"

BS = chr(92)   # backslash
TAB = chr(9)
BT = chr(96)   # backtick

NEW_TITLE = "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry"
OLD_TITLE = ("Gradient Structure Laws as Predictors of PEFT Design: "
             "Zero-Shot Cross-Architecture Rank Allocation")
HEADING = "## P3（" + BT + "PRLETTERS-D-26-02378" + BT + "）Revise（2026-10-12）"


def build_entry() -> str:
    """Return the markdown entry, with backslashes assembled from chr(92)."""
    t = BS + "title"
    return "\n".join([
        "> **📮 2026-10-15 12:54 —— P3 修订稿（" + BT + "PRLETTERS-D-26-02378R1" + BT
        + "）状态 = " + BT + "With Editor" + BT + "；修订稿标题已换**",
        ">",
        "> **来源**：操作者提供的 Editorial Manager 列表行（**未见截图**，逐字照录）：",
        ">",
        "> | Manuscript Number | Title | Submitted | Status Date | Current Status |",
        "> |---|---|---|---|---|",
        "> | **" + BT + "PRLETTERS-D-26-02378R1" + BT + "** | **" + NEW_TITLE
        + "** | **Oct 13, 2026** | **Oct 14, 2026** | **" + BT + "With Editor" + BT + "** |",
        ">",
        "> ### 一、✅ 三件事因此确认",
        ">",
        "> 1. **修订稿已进入系统并被编辑接手**：状态 " + BT + "With Editor" + BT
        + "（状态日期 **Oct 14, 2026**）。",
        ">    稿号带 **" + BT + "R1" + BT + "** 后缀 ⇒ 这是**修订版**，与首投 "
        + BT + "PRLETTERS-D-26-02378" + BT + " 同一稿号序列。",
        "> 2. **修订稿标题已换**：由首投的 *" + OLD_TITLE + "*（**97 字符**）改为",
        ">    ***" + NEW_TITLE + "*（67 字符）**。",
        ">    **✅ 本地已核实是「计划内改动」，不是传错版本**：",
        ">    " + BT + "SUBMISSION/P3_PRL_revision/manuscript/latex_source/main.tex" + BT
        + " 的 " + BT + BS + "title{...}" + BT,
        ">    **与 EM 行逐字一致**；13 页完整版存档 " + BT + "main_full.tex" + BT
        + " 仍留旧标题（末尾带 " + BT + "(full version)" + BT + "）",
        ">    ⇒ 换标题是**投稿件（10 页）专属的压缩动作**，存档未动。",
        "> 3. **投稿日**：**Oct 13, 2026**（修订包于 2026-10-13 建，见 " + BT + "文件地图.md" + BT
        + "）⇒ 与包内时间线自洽。",
        ">",
        "> ### 二、⚠️ 只记录、不推断的部分（避免第二次「滞后显示」式误判）",
        ">",
        "> * " + BT + "With Editor" + BT + " 的**日期是 Oct 14**，即投稿次日；"
        + "**但 Oct 13 那一格里有没有过别的状态，我们不知道**",
        ">   （EM 列表只给当前状态 + 状态日期，不给历史）。",
        "> * **修订稿是否直接送回原审稿人，无法从这一行判断**。两种可能都留着：",
        ">   ① 编辑先处理（技术检查 / 与 33 条应答对齐）再送审；② 编辑已决定不再外审。",
        ">   再送审的实证只能来自下次状态变化（出现 " + BT + "Under Review" + BT + " = 走 ①）。",
        "> * **deadline " + BT + "2026-11-02" + BT + " 的含义**：那是**作者**修回截止日，**已履行**；",
        ">   它**不是**审稿期限，**不再用于预估出结果时间**。",
        "> * ⛔ 本轮**不更新**「首轮决定预计 2026-10 下旬」那条预估——它的依据是 A1 单点样本（29 天），",
        ">   与「是否再送审」无关；等下一次状态变化再谈。",
        ">",
        "> ### 三、下一步（无新增待办）",
        ">",
        "> 修订稿已交、应答已逐条写（33/33）、证据包已归档 ⇒ **本条不产生新动作**，",
        "> 唯一下一步是**等下一次状态变化**（" + BT + "Under Review" + BT + " / "
        + BT + "Decision" + BT + "）。",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ---- the facts must still check out against the repo before anything is written ----
    assert TEX.exists(), f"missing {TEX}"
    tex = io.open(TEX, encoding="utf-8").read()
    assert BS + "title{" + NEW_TITLE + "}" in tex, "local revision title != the EM row title"

    ent = build_entry()
    assert TAB not in ent, "entry contains a TAB character"
    assert BT + BS + "title{...}" + BT in ent, "entry lost the literal backslash before 'title'"
    assert "Oct 14, 2026" in ent and "With Editor" in ent
    mark = ent.splitlines()[0]

    for name, prepend in ((HANDOFF.name, True), (MAP.name, False)):
        p = REPO / name
        text = io.open(p, encoding="utf-8").read()
        stale = ("的 " + BT + TAB + "itle{...}" + BT) in text
        if stale:
            # A damaged insertion exists. Restoring from git is the only safe repair: the first
            # version of this script tried to delete the block in place, and its "skip blank lines"
            # rule ran past the end of the entry and cut the head off the next one (it removed the
            # "2026-10-16 01:00" heading and three of its bullets). Nothing here rewrites history:
            # git holds the file without the insertion, so the insertion is simply redone on top.
            raise SystemExit(
                f"  {name}: contains a damaged insertion -- run `git checkout -- {name}` first, "
                "then re-run this script (in-place repair is unsafe)")
        if mark in text:
            print(f"  {name}: already correct, skipping")
            continue
        if prepend:
            i = text.find("# 项目交接文档")
            assert i >= 0, "HANDOFF.md heading not found"
            j = text.find("\n", i)
            text = text[: j + 1] + "\n" + ent + text[j + 1:]
        else:
            assert text.count(HEADING) == 1, "expected exactly one P3 heading in the map"
            text = text.replace(HEADING, HEADING + "\n\n" + ent, 1)
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(text)

    print("  (dry run)" if not a.apply else "  applied")
    base_lines = {HANDOFF.name: None, MAP.name: None}
    add = len(ent.split("\n"))
    for name in (HANDOFF.name, MAP.name):
        text = io.open(REPO / name, encoding="utf-8").read()
        ok_mark = mark in text
        ok_bs = BT + BS + "title{...}" + BT in text
        ok_tab = ("的 " + BT + TAB + "itle{...}" + BT) not in text
        print(f"  {'OK ' if ok_mark else 'BAD'} {name}: entry | {'OK ' if ok_bs else 'BAD'} literal "
              f"{BS}title | {'OK ' if ok_tab else 'BAD'} no damaged line")
    # The earlier in-place repair silently truncated the following entry, so assert that the
    # neighbours of the insertion are intact rather than trusting the length alone. Only meaningful
    # once the files were actually written.
    if not a.apply:
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read().split("\n")
    assert h[0].startswith("# 项目交接文档"), "HANDOFF title line moved"
    assert mark in h[2], "entry is not the first block after the title"
    assert mark in h[1] + h[3] or h[1] == "", "entry is not preceded by the expected blank line"
    assert any("按操作者要求重排任务" in ln for ln in h), "the 2026-10-16 entry was lost"
    assert any("LABELS VERIFIED" in ln for ln in h), "the 2026-10-16 LABELS bullet was lost"
    m = io.open(MAP, encoding="utf-8").read().split("\n")
    n_heading = [i for i, ln in enumerate(m) if ln == HEADING]
    assert len(n_heading) == 1, "P3 heading no longer unique in the map"
    assert m[n_heading[0] + 2].startswith("> **📮 2026-10-15 12:54"), "map entry not under the P3 heading"
    assert any("P3 修订包（PRL Revise，2026-10-13 建）" in ln for ln in m), "map P3 subsection lost"
    print("  neighbours verified: HANDOFF title+entry+old entry, map heading+entry+subsection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
