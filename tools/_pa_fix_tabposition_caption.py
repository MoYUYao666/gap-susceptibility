# -*- coding: utf-8 -*-
r"""修 `tab:position` 表注里"MS-COCO reverses that ordering"这一**无据主张**（2026-10-10）。

## 证据（实测）

`tab:position` 的 COCO 行三值同源（`outputs/coco/rq2_*`）：

| 臂 | ΔCG |
|---|---|
| **`text_only`** | **−0.041** ← 表里加粗 |
| `both` | −0.052 |
| `vision_only` | +0.031 |

**`text_only` 的间隙增长最小** → **与 Flickr30k 同向，没有反转**。
**表注却写 "MS-COCO reverses that ordering"** → **与表自身的数据矛盾**。

**真正的反转在 SigLIP**（`validation.tex`，严格冻结协议）：`text_only` **+0.066±0.006** vs
`both` **−0.011±0.006**（配对差 −0.078，t = −52.7，5 seed 同号）。

## 改法

表注改为：**四个数据集上 text-only 都是最保护**，**并明确指出反转发生在 SigLIP 上**
（引 `sec:validation`），避免读者以为 COCO 会反转。

    python tools\_pa_fix_tabposition_caption.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = ("Text-only gives the smaller gap increase on Flickr30k, BLIP-1 and ViT-L, "
       "while MS-COCO reverses that ordering.")

NEW = ("Text-only gives the smaller gap increase on every dataset in the table: "
       "Flickr30k, MS-COCO, BLIP-1 and ViT-L. The ordering does reverse, but on SigLIP "
       "rather than on a second dataset, and under the strict-freezing control rather than "
       "under this convention (Section~\\ref{sec:validation}).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} 处 ===")
    if n != 1:
        i = t.find("MS-COCO reverses")
        print("  实际文本:", repr(t[max(0, i - 220):i + 120]) if i > 0 else "(未找到)")
        return 1
    t2 = t.replace(OLD, NEW, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    assert "MS-COCO reverses" not in t3, "旧主张仍在"
    for k in ("every dataset in the table", "on SigLIP", "strict-freezing control"):
        assert k in t3, f"断言失败：缺 {k}"
    print("  ✅ 表注已修：改为「四个数据集都是 text-only 最保护」+ 指明反转在 SigLIP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
