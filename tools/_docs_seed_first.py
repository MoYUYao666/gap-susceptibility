# -*- coding: utf-8 -*-
r"""落账：第一批补 seed 结果（2026-10-08 23:30）。

    python tools\_docs_seed_first.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-08 23:30 —— 第一批补 seed 结果：排序稳定，且**效应量比参照更锐利****
>
> ### CLIP B/32 @ r4（补到 3 seed）
>
> | 臂 | CGΔ 均值 | sd | 各 seed |
> |---|---|---|---|
> | **text_only** | **−0.0288** | **±0.0013** | [−0.0274, −0.0297, −0.0295] |
> | both | −0.0188 | ±0.0004 | [−0.0192, −0.0186, −0.0186] |
> | vision_only | +0.0124 | 单 seed（跑中） | [+0.0124] |
>
> **判定：排序未翻转**（`text_only` 最保护）✅；两臂 sd 区间**完全不重叠**（差 0.010 ≈ **7.7 倍 sd**）。
>
> ### ⚠️ 一处自我修正
>
> 我先前用 **sd ≈ 0.0030** 作参照——**那是 CLIP B/32 r8 的跨臂 sd**。
> **逐臂 sd 实测只有 0.0013–0.0044** → **效应比我先前说的更锐利**；
> 对 OpenCLIP「仅约 2 sd」的担忧用的也是偏保守的参照，**补完 seed 后须重算**。
>
> ### ⚠️ 时间估计又一次偏乐观
>
> `both` 臂实测 **55 min**（我估 10–20 min）→ **18 run ≈ 10–12 h**（不是 4–5 h）。
> **规律**：`both` 与 `vision_only` 臂**远慢于** `text_only`
> （可训张量多、反传路径长）。**→ 将来对严格冻结 run 估时，应按 `both` 的 55 min 而非 `text_only` 的 10 min。**
>
> ### 当前 seed 覆盖
>
> | 骨干 | text_only | both | vision_only |
> |---|---|---|---|
> | CLIP B/32 @ r8（归档） | 5 ✅ | 5 ✅ | 5 ✅ |
> | **CLIP B/32 @ r4** | **3** ✅ | **3** ✅ | 1（跑中） |
> | CLIP B/16 @ r4 | 1 | 1 | 1 |
> | OpenCLIP @ r4 | 1 | 1 | 1 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "第一批补 seed 结果" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("第一批补 seed 结果", "−0.0288", "7.7 倍 sd", "18 run ≈ 10–12 h"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
