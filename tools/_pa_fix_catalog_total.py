# -*- coding: utf-8 -*-
r"""修目录表 Total：374 → 212（表内各类之和），并更正附录的构成说明（2026-10-05）。

## 问题

`tools/_pa_add_strictfreeze_to_catalog.py` 把目录表 Total 由 **117** 改成 **374**，
用的是"117 + 162 ODE + 95 严格冻结"的**全文口径**。

**但那张表只列"按类别的实验目录"，不含 ODE 拟合。** 于是：

| 版本 | 各类求和 | 表中 Total | 自洽 |
|---|---|---|---|
| 改动前 | 117 | 117 | ✅ |
| **改动后** | **212**（117 + 95） | **374** | **❌ 不一致** |

**正确**：表内 Total 应 = 各类求和 = **212**。
（`tools/_check_catalog_sum.py` 会核算并断言。）

## 同时更正附录的构成说明

改动后写的"117 mechanism experiments from Part I, 162 ODE-fitting runs, and 95 strict-freezing
controls"——**把严格冻结既算进目录又单列，重复计数**。正确构成：

| 组 | 数 |
|---|---|
| 附录目录（13 类机理 + 第 XIV 类严格冻结） | **212** |
| ODE 拟合（`validation.tex`） | 162 |
| **全文合计** | **374** |

## 全文 374 是对的

其余各处（摘要、introduction、empirical、conclusion、validation）的 **374** 用全文口径，
**正确，不动**。

    python tools\_pa_fix_catalog_total.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"

OLD_TOTAL = "\\textbf{Total} & \\textbf{374} \\\\"
NEW_TOTAL = "\\textbf{Total} & \\textbf{212} \\\\"

OLD_TEXT = ("Table~\\ref{tab:full_experiments} lists all 374 experiments reported in this paper: 117 "
            "mechanism experiments from Part~I, 162 ODE-fitting runs, and 95 strict-freezing controls. "
            "The last group is the one on which the adaptation-position findings rest, since only under "
            "strict freezing do the arms differ solely in where the adapters sit.")
NEW_TEXT = ("Table~\\ref{tab:full_experiments} catalogues the 212 runs that are listed here by section, "
            "the 117 mechanism experiments of Part~I together with the 95 strict-freezing controls; a "
            "further 162 ODE-fitting runs are catalogued in Section~\\ref{sec:validation}, giving 374 in "
            "total. The strict-freezing group is the one on which the adaptation-position findings rest, "
            "since only under strict freezing do the arms differ solely in where the adapters sit.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(SUP, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_TOTAL, NEW_TOTAL, "Total 行 374 → 212"),
                          (OLD_TEXT, NEW_TEXT, "附录构成说明（去掉重复计数）")):
        if old in t:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ {why}：未命中")
    if apply and n:
        io.open(SUP, "w", encoding="utf-8", newline="").write(t)
        print(f"\n  ✅ 已写回（{n} 处）")
    elif not apply:
        print(f"\n  {n}/2 处可改（预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
