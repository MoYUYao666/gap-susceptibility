# -*- coding: utf-8 -*-
r"""修正 HANDOFF 页数标注里的 3 个 `?`（2026-10-06）。

## 问题

上一版脚本的措辞取自**同一行**的 `NC (\d+) 页`，但有两行的写法不同：

| 行 | 原写法 | 为何没匹配 |
|---|---|---|
| L313 | `已重建（**45 页**）` | 前面**没有 "NC"** |
| L320 | `` `pdfinfo main_nc.pdf` = **45 页** `` | 页面数前有反引号与空格 |
| L2155 | 上下文**根本没有 NC 页数**（是 P1 整改条目） | **不该标** |

## 修法

- 前两处：取**上文最近一行的 45**，把 `? → 49` 改为 `45 → 49`；
- L2155：**整条标注删除**（无依据的断言，宁可没有）。

    python tools\_docs_handoff_fix_qmark.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "HANDOFF.md"


def main() -> int:
    apply = "--apply" in sys.argv
    lines = io.open(F, encoding="utf-8").read().splitlines(keepends=True)
    out, fixed, removed = [], 0, 0
    for i, ln in enumerate(lines):
        if "? → 49" in ln:
            # 从上面 6 行里找最近一个页数
            src = None
            for j in range(i - 1, max(-1, i - 7), -1):
                m = re.search(r"\*{0,2}(\d{2,3})\s*页", lines[j])
                if m:
                    src = m.group(1)
                    break
            if src in ("45", "43"):
                out.append(ln.replace("? → 49", f"{src} → 49"))
                fixed += 1
            else:
                removed += 1          # 无依据 → 删整条
                continue
        else:
            out.append(ln)
    print(f"  修正 {fixed} 处（补上来源页数）｜ 删除 {removed} 处（上下文无依据）")
    if not apply:
        print("  （预演）")
        return 0
    t = "".join(out)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "? → 49" not in t2, "仍有未修正的 ? 标注"
    assert "45 → 49" in t2, "应含 45 → 49"
    print(f"  ✅ 已修正并断言通过（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
