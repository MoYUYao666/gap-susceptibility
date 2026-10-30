# -*- coding: utf-8 -*-
r"""同步 `文件地图.md` 的 P3 状态（2026-10-07 晚：回到 Under Review）。

L18 现写着「**🔴 该行已于 2026-10-07 更正**——当时记为仍 Under Review 系**滞后显示**，
实际自 10-06 起为 `Required Reviews Completed`」——**该推断已于当晚被推翻**，需就地标注。

    python tools\_docs_filemap_p3_1007pm.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "文件地图.md"

OLD = ("**🔴 该行已于 2026-10-07 更正**——当时记为仍 Under Review 系**滞后显示**，"
       "实际自 10-06 起为 **`Required Reviews Completed`**（10-07 EM 记录显示同一状态日期为该状态）。")
NEW = ("**🔴 该行已于 2026-10-07 更正**——当时记为仍 Under Review 系**滞后显示**，"
       "实际自 10-06 起为 **`Required Reviews Completed`**（10-07 EM 记录显示同一状态日期为该状态）。\n"
       "> **🔴🔴 上述更正于 2026-10-07 晚又被推翻**：当日晚的 EM 记录显示**同一状态日期（`Oct 06, 2026`）"
       "为 `Under Review`** → **状态在同一日期下往返过**，故\"滞后显示\"的推断**无法确定**。\n"
       "> **→ 现状（2026-10-07 晚）：P3 = `Under Review`**；`Under Review` 与 `Required Reviews Completed` "
       "**各有一次观测**，两种解释（真往返 / 列表显示不一致）**均不排除**。详见 `HANDOFF.md` 2026-10-07 晚条目。")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "上述更正于 2026-10-07 晚又被推翻" in t:
        print("  已更新，跳过")
        return 0
    if OLD not in t:
        print("  ⚠ 未命中锚点")
        return 1
    print("  ✅ 命中 P3 更正行")
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("上述更正于 2026-10-07 晚又被推翻", "状态在同一日期下往返过", "现状（2026-10-07 晚）：P3 = `Under Review`"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ 已更新并断言通过（{len(t2.splitlines())} 行）")

    # 全量一致性核对
    print("\n  === 三份文档 P3 现状一致性 ===")
    for f in ("HANDOFF.md", "文件地图.md", "哪篇是哪篇.md"):
        s = io.open(REPO / f, encoding="utf-8").read()
        has_ur = "Under Review" in s
        has_rrc = "Required Reviews Completed" in s
        has_note = "往返" in s
        print(f"    {f:<18} Under Review {has_ur} ｜ Required Reviews {has_rrc} ｜ 已标注往返 {has_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
