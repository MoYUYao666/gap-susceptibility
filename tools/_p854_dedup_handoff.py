# -*- coding: utf-8 -*-
r"""Remove the duplicated stage entry from HANDOFF.md, keeping the richer copy.

Two copies of the stage entry exist because a re-run of tools/_p850 re-inserted the block beside the
updated one. Copy A (at line ~40) ends with "### 五、commit"; copy B (after it) ends with
"### 六、commit" and additionally carries the "### 五、实测时间" section. B is the union of both, so A
is the one to drop.

Two earlier attempts at this failed for instructive reasons, both recorded here:
* keying on a distinctive title string failed because I had already edited that title in the file, so
  the "stale" marker matched nothing;
* an in-place "skip blank lines until the next heading" deletion ran past the end of the block.

So this version identifies the copies by *line number* after printing them, asserts that the span to
delete contains only blockquote lines and blanks, and asserts the survivors afterwards.

    python tools/_p854_dedup_handoff.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
ENTRY = "> **🖥️ 2026-10-15 13:02 —— COCO 三个 seed 已全部完成；GPU 队列交给 LLaVA；进度脚本两个读数缺陷已修**"
NEXT = "> **🔄 2026-10-16 01:00 —— 按操作者要求重排任务；labels bug 修复；4-bit 噪声地板已量化**"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    text = io.open(HANDOFF, encoding="utf-8").read()
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln == ENTRY]
    print(f"  stage-entry copies at lines: {[i + 1 for i in starts]}")
    if len(starts) <= 1:
        print("  nothing to deduplicate")
        return 0
    assert len(starts) == 2, "expected exactly two copies"
    first, second = starts

    # Keep the copy that carries "### 五、实测时间" (the union), drop the other.
    keep_timing_first = any(ln == "> ### 五、实测时间" for ln in lines[first:second])
    print(f"  first copy has 实测时间: {keep_timing_first}")
    assert not keep_timing_first, "the timing section is in the first copy; refusing to guess"
    drop_start, drop_end = first, second

    # delete the first copy plus the blank run that separated the copies
    end = drop_end
    while end > 0 and lines[end - 1] == "":
        end -= 1
    removed = lines[drop_start:end]
    bad = [ln for ln in removed if ln and not ln.startswith(">")]
    assert not bad, f"refusing to delete non-quote lines: {bad[:2]}"
    print(f"  would delete lines {drop_start + 1}-{end} ({len(removed)} lines)")

    if not a.apply:
        print("  (dry run)")
        return 0

    kept = [ln for i, ln in enumerate(lines) if not (drop_start <= i < end)]
    # exactly one blank line between entries
    out = "\n".join(kept)
    while "\n\n\n" in out:
        out = out.replace("\n\n\n", "\n\n")

    ml = out.split("\n")
    assert out.count(ENTRY) == 1, "expected exactly one stage entry after dedup"
    assert ml[2].startswith("> **📮 2026-10-15 12:54 —— P3 修订稿"), "P3 entry is no longer first"
    assert any(ln == NEXT for ln in ml), "the 2026-10-16 entry lost its heading"
    assert "LABELS VERIFIED" in out, "the 2026-10-16 LABELS bullet was lost"
    for k in ("### 五、实测时间", "### 六、commit", "0.5823 ± 0.0002", "0.5655 ⇒ 0.5823",
              "13:02:42", "3/3"):
        print(f"  {'OK ' if k in out else 'CHECK'} {k}")
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(out)
    print(f"  applied: {len(ml)} lines (was {len(lines)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
