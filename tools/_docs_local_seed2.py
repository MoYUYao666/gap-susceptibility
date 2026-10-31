# -*- coding: utf-8 -*-
r"""落账：本地补 seed 首个完成 + 时间估计的**第 3 次修正**（2026-10-09 17:35）。

    python tools\_docs_local_seed2.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-09 17:35 —— 本地补 seed：B/16 `both` 完成，**排序未翻转**；时间估计第 3 次修正**
>
> ### 进度（16:05 启动 → 17:29，已 84 min）
>
> | 骨干 | text_only | both | vision_only |
> |---|---|---|---|
> | CLIP B/32 r4 | ✅ 齐 | ✅ 齐 | ✅ 齐 |
> | **CLIP B/16 r4** | ✅ 齐 | ✅ **齐（16:05→17:23，78 min）** | ⏳ 跑中 |
> | OpenCLIP r4 | 待 | 待 | 待 |
>
> ### ✅ 新 run 的质量（**排除云端那种失效**）
>
> `both`/seed456：**`R@1 = 0.7140`**、`loss 末 = 0.0709`、`n_trainable = 245,760` ✅
> （云端失效时是 `R@1 = 0.002`、`loss = 4.81`）
>
> ### ✅ 排序稳定性：**三骨干全部未翻转**（风险 #1 判据）
>
> | 骨干 | text_only | both | vision_only | 判定 |
> |---|---|---|---|---|
> | CLIP B/32 r4（3 seed） | **−0.0288 ± 0.0013** | −0.0188 ± 0.0004 | +0.0127 ± 0.0024 | ✅ |
> | **CLIP B/16 r4（3 seed）** | **−0.0172 ± 0.0021** | **+0.0107 ± 0.0056** | +0.0403 ± 0.0043 | ✅ |
> | OpenCLIP r4（1 seed） | +0.0798 | +0.0860 | +0.1019 | ✅ |
>
> **且 9 个 (骨干,臂) 的 `n_trainable` 全部一致**（98,304 / 245,760 / 147,456）
> → **无口径漂移**（`tools/_p75_new_seed_check.py`）。
>
> ⚠️ **一处需要注意**：B/16 `both` 的均值从 +0.0139（2 seed）变为 **+0.0107**（3 seed），
> **sd 从 0.0016 升到 0.0056** → **新 seed 的离散度更大**。**但排序未变。**
>
> ### ⏱️ 时间估计**第 3 次修正**（规律：我每次都低估）
>
> | 估计次序 | 我的说法 | 实际 |
> |---|---|---|
> | 第 1 次 | 18 run ≈ **4 h** | 实际 55 min–3 h/run |
> | 第 2 次 | 剩 14 缺口 ≈ **15–40 h** | — |
> | 第 3 次 | 剩 8 缺口 ≈ **2–2.5 h** | **`both` 实测 78 min**（非 40 min） |
>
> **修正后的真实估计**：
>
> | 臂 | batch 128 | **batch 64（本次，实测）** |
> |---|---|---|
> | `text_only` | ≈10 min | **≈20 min** |
> | `both` | ≈26 min | **≈78 min** |
> | `vision_only` | ≈30 min | **≈40 min** |
>
> **剩余 6 个 OpenCLIP run ≈ 126 min/臂 × 2 臂 + 3 臂 ≈ 5–6 h**
> （不是我先说的 2–2.5 h）。
>
> ### ⚠️ batch 64 的**代价必须标注**
>
> **B/16 的 3 个 seed 里，seed456 是 batch 64 跑的，seed42/seed123 是 batch 128**
> → **同一骨干内混了两个 batch 口径**。
> **处置**：① 在归档与文档中显式标注；② 结论只用**排序方向**（跨 batch 稳健），
> **不用绝对值**（跨 batch 不可比）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "本地补 seed：B/16 `both` 完成" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("B/16 `both` 完成", "R@1 = 0.7140", "时间估计**第 3 次修正**",
              "≈78 min", "同一骨干内混了两个 batch 口径"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
