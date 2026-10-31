# -*- coding: utf-8 -*-
r"""Mark docs/P3_REVIEW_RESPONSE.md as post-submission and link it to the archived status row.

The working review-response document still described the revision as pending ("修订截止 2026-11-02").
That deadline has now been met: the revision was submitted on 2026-10-13 and the system shows
`With Editor` with a status date of 2026-10-14. A reader of that document would otherwise think the
revision is still owed.

Deliberately NOT touched: docs/P3_RESPONSE_LETTER.md and the revision package under
SUBMISSION/P3_PRL_revision/. Those are the submitted artefacts; their text must stay exactly as
uploaded, so nothing here rewrites them.

Backslashes are assembled from chr(92) and the inserted block is asserted to contain no TAB, because
an earlier script in this same session lost `\t` on the way into the file and corrupted two documents.

    python tools/_p849_p3_submitted_note.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "P3_REVIEW_RESPONSE.md"
BT = chr(96)
TAB = chr(9)
ANCHOR = "> **状态日期**：2026-10-12｜**修订截止**：**2026-11-02**（逾期视为撤稿）"
MARK = "已交稿，状态 = " + BT + "With Editor" + BT


def head_commit() -> str:
    r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def build_block(commit: str) -> str:
    # No leading blank line: the header is one continuous blockquote, and an empty line would split it
    # in two so the "编辑/总评/平台要求" lines would read as a separate quote.
    return "\n".join([
        "> **📮 2026-10-15 12:54 更新——修订稿已交，状态 = " + BT + "With Editor" + BT + "**",
        "> **投稿日 2026-10-13**（系统 Submitted）｜**状态日期 2026-10-14**｜"
        "稿号 **" + BT + "PRLETTERS-D-26-02378R1" + BT + "**",
        "> ⇒ 上条" + BT + "2026-11-02" + BT + "截止**已履行**，本文档由「待回复」转为**存档**；"
        "后续只看状态变化。",
        "> 落账位置：" + BT + "HANDOFF.md" + BT + " 顶部 2026-10-15 条目、"
        + BT + "文件地图.md" + BT + " → P3 Revise 小节（提交 " + commit + "）。",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    text = io.open(DOC, encoding="utf-8").read()
    block = build_block(head_commit())
    assert TAB not in block, "inserted block contains a TAB"
    if MARK in text:
        print("  already recorded")
        return 0
    assert text.count(ANCHOR) == 1, f"expected exactly one status anchor, found {text.count(ANCHOR)}"
    new = text.replace(ANCHOR, ANCHOR + "\n" + block, 1)
    assert new != text
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(DOC, "w", encoding="utf-8", newline="").write(new)

    check = io.open(DOC, encoding="utf-8").read()
    # MARK spans a line break in the document, so test the two halves separately.
    for k in ("📮 2026-10-15 12:54 更新", BT + "With Editor" + BT, "2026-10-13",
              "2026-10-14", "PRLETTERS-D-26-02378R1", ANCHOR):
        print(f"  {'OK ' if k in check else 'BAD'} {k[:48]}")
    assert TAB not in check, "a TAB entered the document"
    lines = check.splitlines()
    i = lines.index(ANCHOR)
    assert lines[i + 1].startswith("> **📮 2026-10-15 12:54"), "note is not directly after the status line"
    assert lines[i + 5] == "> **编辑**：Yonghuai Liu（Editor-in-Chief）", "header blockquote was split"
    print("  header blockquote verified unbroken")
    print(f"  lines = {len(lines)} (was {len(text.splitlines())})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
