# -*- coding: utf-8 -*-
r"""修正 `fig14` 图注的"reaches frozen-level CG"（重绘时断言捕获，2026-10-05）。

## 问题

**正文**（`supplement.tex` fig14 图注）：

> "Training an Adapter on the text side only **reaches frozen-level CG** while its text+vision
> counterpart does not"

**源数据**（`outputs/adapter_layered_results.json`，各配置末行）：

| 配置 | CG | R@1 | 与 Frozen 的 CG 差 |
|---|---|---|---|
| Frozen | 0.8143 | 0.6850 | — |
| **Adapter Text-only** | **1.0644** | **0.0600** | **+0.250** |
| Adapter Text+Vis | 1.3168 | 0.0050 | +0.503 |

**Text-only 的 CG 比 frozen 高 0.250** —— **不是"frozen-level"**。
正确表述：**两者的 CG 都高于 frozen；text-only 的升幅约为 text+vision 的一半**。

## 同时保留原图注中**正确**的部分

原图注另有两点是**对的**，须保留：
1. "**this is a layered-configuration comparison**"；
2. "**the aggregate cross-dimension comparison in Section~\ref{sec:validation} does not reproduce a
   text-only advantage for Adapter**" —— 与 `outputs/analysis/adapter_common_baseline.json` 的发现一致
   （Adapter 上 text-only 无优势）。**这两句是本文诚实披露的关键，不能连带删掉。**

    python tools\_pa_fix_fig14_caption.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD = ("Training an Adapter on the text side only reaches frozen-level CG while its text+vision "
       "counterpart does not; this is a layered-configuration comparison, and the aggregate "
       "cross-dimension comparison in Section~\\ref{sec:validation} does not reproduce a text-only "
       "advantage for Adapter.")

NEW = ("Both Adapter configurations raise the gap above the frozen reference ($0.81$), the text-side one "
       "by $0.25$ and its text+vision counterpart by $0.50$, and both collapse retrieval to near zero "
       "($R@1$ $0.06$ and $0.005$); this is a layered-configuration comparison, and the aggregate "
       "cross-dimension comparison in Section~\\ref{sec:validation} does not reproduce a text-only "
       "advantage for Adapter.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中 'reaches frozen-level CG' 图注")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "reaches frozen-level CG" not in t2, "旧说法仍在"
        for k in ("0.25", "0.50", "0.06", "does not reproduce a text-only "
                  "advantage for Adapter"):
            assert k in t2, f"断言失败：缺 {k}"
        print("  ✅ 已改并断言通过（保留了两点正确的披露）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
