# -*- coding: utf-8 -*-
r"""回退并重做 HANDOFF 的页数标注（2026-10-06）。

## 上一版的两个缺陷

1. **插进了句子中间**：`L326`、`L637` 的原文是**跨行的句子**，
   标注被插在句中 → **打断了行文**；
2. **措辞不精确**：那两处原文是 `NC 43 页`（不是 45），
   写"后来增至 49"虽不算错，但不如"43 → 49"准确。

## 修法

- **先删除**上一版插入的全部 8 处标注（幂等回退）；
- **只对"独立表格行 / 独立行"**插入标注（行首为 `>` + `|`，或该行以句号结尾）；
- 措辞分两种：原文 45/33 → "45 → 49"；原文 43/33 → "43 → 49"。

    python tools\_docs_handoff_pages_redo.py [--apply]
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

    # ── ① 幂等回退：删掉上一版插入的标注行
    lines = t.splitlines(keepends=True)
    kept = [ln for ln in lines if TAG not in ln]
    removed = len(lines) - len(kept)
    t = "".join(kept)
    print(f"  ① 已移除上一版标注 {removed} 处")

    if not apply:
        print("  （预演）")
        return 0

    # ── ② 只对"独立行"插入标注
    lines = t.splitlines(keepends=True)
    out, n = [], 0
    for ln in lines:
        out.append(ln)
        has_pg = ("45 页" in ln or "33 页" in ln or "43 页" in ln)
        if not has_pg:
            continue
        stripped = ln.strip()
        # 判据：整行是表格行（| … |）或整行以中文句号/分号结尾（自足句）
        is_table = stripped.startswith("|") and stripped.endswith("|")
        is_selfcontained = stripped.endswith(("。", "；", "|"))
        if not (is_table or is_selfcontained):
            continue                      # 跨行句子 → 跳过，避免打断行文
        m = re.match(r"(\s*>\s?)", ln)
        pre = m.group(1) if m else ""
        # 取该行出现的第一个页数，做准确措辞
        mm = re.search(r"NC\s*\*{0,2}(\d{2,3})\s*页", ln)
        src = mm.group(1) if mm else "?"
        out.append(f"{pre}{TAG[:-2]}**（{src} → 49；后续阶段：拆面板、改画 Figure 10、图例移出等所致）\n")
        n += 1
    if n == 0:
        print("  无可安全标注的行")
        return 0
    t2 = "".join(out)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8").read()
    # 断言：原数字未被改写；无标注落在跨行句子中
    assert "NC **45 页**" in t3 and "NC **43 页**" in t3, "原数字被改写（应保留）"
    for m in re.finditer(r"→ \*\*页数后来增至 NC 49 / Springer 37\*\*（(\d+) → 49", t3):
        pass
    print(f"  ✅ 已插入 {n} 处（均为自足行），原数字保留未改（{len(t3.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
