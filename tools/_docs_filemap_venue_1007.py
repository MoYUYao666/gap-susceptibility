# -*- coding: utf-8 -*-
r"""补做 `文件地图.md` 待办 2b 的阻塞项更新（2026-10-07）。

上一版脚本在 HANDOFF 断言处中止（`**` 加粗打断断言串），故文件地图未更新。本脚本只做文件地图。

    python tools\_docs_filemap_venue_1007.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "文件地图.md"

OLD = "**⏳ 阻塞项**：候刊 **Guide for authors PDF**"
NEW = ("**✅ 阻塞项已于 2026-10-07 解除**：5 份 Guide 已由操作者提供并存档 `期刊指南/`。\n"
       "   **对照结论**（`docs/PAPERA_VENUE_DECISION.md`，逐字段引原文）：\n"
       "   - ❌ **IVC 出局**：Guide 规定字数控 **4500–7500**，我们约 **11,254 词**，超约 50%\n"
       "   - ❌ **IF 出局**：Research article 页数硬上限 **10–35**，我们约 **45–52 页**；且明示超限可 **desk rejection**（引用 44 条 ✅，限 50）\n"
       "   - ⚠️ **KBS 勉强**：*\"preferably no more than 20 double line spaced manuscript pages\"*，我们约 2.2 倍（**非硬性**）\n"
       "   - ✅ **可行 = ESWA**（首选；无篇幅上限，但**双盲**需拆题名页）／ **CVIU**（次选；无上限 + **单盲**，scope 需自评）\n"
       "   （5 刊其余字段**全部达标**：摘要 ≤250 我们 244 ｜ 关键词 1–7 我们 6 ｜ Highlights 3–5×85 字符 我们 5 条最长 61 ｜ Data 均 Option C）\n"
       "   **⏭ 下一个待办 = 操作者确认选刊（ESWA 或 CVIU）**\n"
       "   ~~原记（已过期）：候刊 Guide for authors PDF（优先 KBS、ESWA、CVIU）——无官方 Guide 无法产出符合本项目标准的对比表~~")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "阻塞项已于 2026-10-07 解除" in t:
        print("  已更新，跳过")
        return 0
    i = t.find(OLD)
    if i < 0:
        print(f"  ⚠ 未命中锚点：{OLD[:40]}")
        return 1
    print("  ✅ 命中待办 2b 阻塞项")
    if not apply:
        print("  （预演）")
        return 0
    # 找到该行末尾（锚点所在整行的结束）
    j = t.find("\n", i)
    line = t[i:j]
    t2 = t[:i] + NEW + t[j:]
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8").read()
    for k in ("阻塞项已于 2026-10-07 解除", "IVC 出局", "IF 出局",
              "可行 = ESWA", "下一个待办 = 操作者确认选刊"):
        assert k in t3, f"断言失败：缺 {k}"
    assert "原记（已过期）" in t3, "旧条目未按规则保留"
    print(f"  ✅ 已更新并断言通过（{len(t3.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
