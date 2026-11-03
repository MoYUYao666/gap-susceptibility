# -*- coding: utf-8 -*-
r"""撤回 `16bb0f5` 里"rank 效应跨骨干成立"的说法，改为经配对检验的表述（2026-10-05）。

## 为什么要改

`16bb0f5` 写入正文：

> "This one does carry across backbones: on SigLIP the same ordering appears, with rank~$8$ reducing the
> gap relative to rank~$4$ by $+0.017$ over five paired seeds ($t = +3.8$), against $+0.019$ on CLIP
> ($t = +8.0$)."

**当时只有 CLIP 与 SigLIP 两个骨干的数据。OpenCLIP 跑完后推翻了这个概括**：

`tools/_pa_rank_analysis.py` 的配对检验（全部严格冻结）：

| 骨干 | 臂 | r8−r4 | t | 方向 |
|---|---|---|---|---|
| CLIP | text_only | −0.0192 | **−7.96** | r8 更小 |
| CLIP | both | −0.0065 | **−2.88** | r8 更小 |
| OpenCLIP | text_only | −0.0112 | **−5.86** | r8 更小 |
| **OpenCLIP** | **both** | **+0.0042** | **+1.09** | r8 更大（**不显著**） |
| SigLIP | text_only | −0.0166 | **−3.79** | r8 更小 |
| SigLIP | both | −0.0204 | **−2.57** | r8 更小 |

→ **5/6 同向且显著，唯一例外不显著** ⇒ 应表述为"**多数组合中同向，但并非无例外**"，
而不是"carry across backbones"。

## 同时补上真正稳健的发现

**位置排序按骨干分组**（10 个骨干 × rank 组合）：CLIP **6/6** 与 OpenCLIP **2/2** 都是
`text_only` 的 ΔCG 更小；**SigLIP 2/2 相反**（`both` 更小）。→ **这才是真正的骨干依赖**。

    python tools\_pa_fix_crossbackbone_claim.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = ("This one does carry across backbones: on SigLIP the same ordering appears, with rank~$8$ "
       "reducing the gap relative to rank~$4$ by $+0.017$ over five paired seeds ($t = +3.8$), against "
       "$+0.019$ on CLIP ($t = +8.0$).")

NEW = ("The direction is not specific to one backbone. Pairing rank~$8$ against rank~$4$ within seeds, "
       "the gap falls on CLIP at the text-only and both positions ($t = -8.0$ and $-2.9$) and on SigLIP "
       "likewise ($t = -3.8$ and $-2.6$); the exception is OpenCLIP at the both position, which moves the "
       "other way by $0.004$ and at $t = +1.1$ is not distinguishable from no change. Five of six "
       "combinations therefore agree, and the dissenting one is the one that carries no significance.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中'跨骨干成立'的旧表述")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("not specific to one backbone", "Five of six", "not distinguishable from no change"):
            assert k in t2, f"断言失败：缺 {k}"
        assert "carry across backbones" not in t2, "旧说法仍在"
        print("  ✅ 已改为配对检验表述并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
