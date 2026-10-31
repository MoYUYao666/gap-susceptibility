# -*- coding: utf-8 -*-
r"""补 limitation：COCO 逐配置表超出本地归档范围（2026-10-07）。

## 为什么单独补

`supplement.tex` 的 `tab:coco_ode`（14 行，text-only r=1..64 + both r=1..64 + Full FT）
声称 **81 recorded runs（14 配置 × 5 seeds + 5 frozen + 5 full-FT）**，
而 `outputs/theory/coco/` 只有 **3 配置 × 3 seeds = 9 runs**。

**我没有改那张表**——改数据表却无归档支撑等同于编造。
**但也不能沉默**：读者拿 `outputs/` 复现时会发现对不上。

**故在 limitation 里如实加一句**，让读者知道该表的来源不在随稿归档内。

    python tools\_pa_ode_limitation2.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

ANCHOR = "the figures quoted should be read as properties of that archived set."
ADD = (" " + "The per-configuration MS-COCO table in the supplement is drawn from a larger set of runs "
       "than the trajectories archived with this work, and should be read on that basis.")

OLD = ("Everything reported in Section~\\ref{sec:validation} is computed from the archived runs and is reproducible "
       "from them; the figures quoted should be read as properties of that archived set.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "per-configuration MS-COCO table in the supplement" in t:
        print("  已补入，跳过")
        return 0
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        i = t.find("archived set")
        print("  实际:", repr(t[max(0, i - 200):i + 80]))
        return 1
    print("  ✅ 命中 limitation 段尾")
    if not apply:
        print("  （预演）")
        return 0
    new = OLD[:-1] + ", while the per-configuration MS-COCO table in the supplement is drawn from a larger " \
                    "set of runs than those archived with this work and should be read on that basis."
    io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, new, 1))
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("per-configuration MS-COCO table in the supplement",
              "read as properties of that archived set"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ 已补入并断言通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
