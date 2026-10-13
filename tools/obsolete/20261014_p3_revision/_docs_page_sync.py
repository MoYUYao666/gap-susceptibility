# -*- coding: utf-8 -*-
r"""按项目规则，把过期页数陈述**标注过期并给新结论**（2026-10-10）。

## 现状（实测）

| 稿 | 实测页数 |
|---|---|
| `paper合` Springer | **40** |
| `paper合` NC | **55** |

**但文档里写过** 39/29、50/33、54——**均过期**。

## 规则（AGENTS.md）

> **追加，不重写**：历史条目保留；**过期结论要标注过期并给出新结论**，不要静默覆盖。

    python tools\_docs_page_sync.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

NOTE_FM = ("\n> **🔄 2026-10-10 页数更新（`paper合`）**：**Springer 版 40 页｜NC 版 55 页**，"
           "0 错误、0 未定义引用、0 Overfull。\n"
           "> 本文件早前记的 **39/29**、**50/33**、**54** 均为**过期数字**（保留以便追溯）；"
           "**以本条与 `HANDOFF.md` 顶部条目为准**。\n"
           "> 门禁 `tools/_claim_ledger.py --apply` = **65/65 通过**。\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    fm = REPO / "文件地图.md"
    t = io.open(fm, encoding="utf-8", errors="replace").read()
    if "2026-10-10 页数更新" in t:
        print("  文件地图已更新，跳过")
    else:
        # 插在 A1 状态块之前（即"二、最容易混的三组"之前）
        i = t.find("## 二、最容易混的三组")
        if i < 0:
            print("  ❌ 未找到插入点")
            return 1
        t2 = t[:i] + NOTE_FM.strip() + "\n\n" + t[i:]
        if a.apply:
            io.open(fm, "w", encoding="utf-8", newline="").write(t2)
            print("  ✅ 文件地图：已加页数更新块")
        else:
            print("  （预演）文件地图将加页数更新块")

    # HANDOFF：把两处 "NC | **54**" 就地标注
    h = REPO / "HANDOFF.md"
    ht = io.open(h, encoding="utf-8").read()
    n = ht.count("| NC | **54** | 0 | 0 | 0 |")
    print(f"\n=== HANDOFF 里 'NC | **54**' 出现 {n} 处 ===")
    if n and a.apply:
        ht2 = ht.replace(
            "| NC | **54** | 0 | 0 | 0 |",
            "| NC | **54**（**2026-10-10 后为 55**，因新增数据集翻转段） | 0 | 0 | 0 |")
        io.open(h, "w", encoding="utf-8", newline="").write(ht2)
        print(f"  ✅ 已就地标注 {n} 处")
    if a.apply:
        for f, tag in ((fm, "文件地图"), (h, "HANDOFF")):
            x = io.open(f, encoding="utf-8", errors="replace").read()
            print(f"  {tag}: 含 '2026-10-10' {'✅' if '2026-10-10' in x else '❌'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
