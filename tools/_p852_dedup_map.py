# -*- coding: utf-8 -*-
r"""Delete the duplicated stage block (items 12-13) that now appears twice in 文件地图.md.

How it happened, recorded because the same trap will recur: the idempotency marker for the map was
the string "12. 🖥️ **GPU 队列（2026-10-15 12:59 状态）**", and tools/_p851 rewrote that header to
"13:02". Restoring the map from a pre-change copy therefore made the marker absent again while the
block was still there, so tools/_p850 re-inserted it and produced two copies.

The fix here is narrow and verifiable: keep the first occurrence of the block, delete later ones, and
assert that the surrounding structure (item 11 above, the "操作者侧待决项" quote below) is intact and
that exactly one copy remains.

    python tools/_p852_dedup_map.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "文件地图.md"
HEAD12 = "12. 🖥️ **GPU 队列（"
HEAD13 = "13. ⚠️ **文档完整性规则（2026-10-15 立）**"
ITEM11 = "11. ⏳ **本轮改动未推 GitHub**"
FOLLOW = "> **操作者侧待决项（2026-09-26 更新）**"


def is_cont(line: str) -> bool:
    """True for a continuation line of item 12/13 (indented, or another numbered item)."""
    return line.startswith("    ") or line.startswith("12. ") or line.startswith("13. ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    lines = io.open(MAP, encoding="utf-8").read().split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith(HEAD12)]
    print(f"  item 12 headers found: {len(starts)} at lines {[i + 1 for i in starts]}")
    if len(starts) <= 1:
        print("  nothing to deduplicate")
        return 0
    assert len(starts) == 2, "expected at most two copies; inspect by hand"

    # The block runs from a "12. …" header to the line before the next non-block line; the copies are
    # adjacent, separated only by a blank line, so delete from the second header to the start of the
    # following content.
    second = starts[1]
    end = second
    while end < len(lines) and (lines[end] == "" or is_cont(lines[end])):
        end += 1
    removed = lines[second:end]
    print(f"  would delete lines {second + 1}-{end} ({len(removed)} lines):")
    for ln in removed[:4]:
        print(f"    {ln[:90]}")
    if not a.apply:
        print("  (dry run)")
        return 0

    kept = lines[:second] + lines[end:]
    text = "\n".join(kept)
    ml = text.split("\n")
    assert sum(1 for ln in ml if ln.startswith(HEAD12)) == 1, "still not exactly one item 12"
    assert sum(1 for ln in ml if ln.startswith(HEAD13)) == 1, "still not exactly one item 13"
    i11 = [i for i, ln in enumerate(ml) if ln.startswith(ITEM11)]
    assert len(i11) == 1, "item 11 lost"
    assert ml[i11[0] + 1].startswith("    `docs/`"), "item 11 lost its second line"
    assert ml[i11[0] + 2] == "", "item 11 lost its blank separator"
    assert ml[i11[0] + 3].startswith(HEAD12), "item 12 no longer follows item 11"
    j13 = [i for i, ln in enumerate(ml) if ln.startswith(HEAD13)][0]
    assert ml[j13 + 1] == "", "item 13 lost its trailing blank line"
    assert ml[j13 + 2].startswith(FOLLOW), "the following quote block moved"
    io.open(MAP, "w", encoding="utf-8", newline="").write(text)
    print(f"  applied: {len(ml)} lines (was {len(lines)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
