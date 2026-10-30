# -*- coding: utf-8 -*-
r"""给 HANDOFF 的**中间阶段页数**标注终值（2026-10-06）。

## 问题

HANDOFF 是**按日期追加**的日志。本轮各阶段留下了不同页数：

| 条目 | 当时页数 | 是否当时为真 |
|---|---|---|
| Times 字体 + 尺寸对齐 | NC **45** / Springer **33** | ✅ 真 |
| 附录 B 修两张坏图 | NC 45 → **48** | ✅ 真 |
| 拆 1×3 面板为单面板 | NC **47** / Springer **36** | ✅ 真 |
| 换回两张图数据 + 竖排 | NC **48** | ✅ 真 |
| 图例移出 + 全量排查 | NC **49** / Springer **37** | ✅ 真（**终值**） |

**每条当时都真**，但**从头读会误以为 45/33 是现状**（项目规则：
「过期结论要**标注过期并给出新结论**，不要静默覆盖」，本仓库多次因"旧条目未标注"而误读状态）。

## 修法

**就地追加**一行 `→ **页数已增至 NC 49 / Springer 37**（后续阶段所致）`，
**保留原数字**（历史为真，不改写）。

    python tools\_docs_handoff_supersede_pages.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "HANDOFF.md"
TAG = "→ **页数后来增至 NC 49 / Springer 37**"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    lines = t.splitlines(keepends=True)
    n = 0
    out = []
    for i, ln in enumerate(lines):
        out.append(ln)
        # 命中"45 页"或"33 页"且尚未标注
        if ("45 页" in ln or "33 页" in ln) and TAG not in ln:
            # 找到该行的缩进前缀（HANDOFF 用 "> " 引用块）
            m = re.match(r"(\s*>\s?)", ln)
            pre = m.group(1) if m else ""
            out.append(f"{pre}{TAG}（后续阶段：拆面板、改画 Figure 10、图例移出等所致）\n")
            n += 1
    if n == 0:
        print("  无未标注的旧页数（或已标注）")
        return 0
    if not apply:
        print(f"  将有 {n} 处标注（预演）")
        return 0
    t2 = "".join(out)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8").read()
    assert t3.count(TAG) == n, "标注数不符"
    assert "NC **45 页**" in t3, "原数字被改写（应保留）"
    print(f"  ✅ 已标注 {n} 处；原数字保留未改（{len(t3.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
