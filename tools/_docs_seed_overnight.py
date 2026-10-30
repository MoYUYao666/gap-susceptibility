# -*- coding: utf-8 -*-
r"""落账：整夜补 seed 结果（2026-10-09 06:00）。

    python tools\_docs_seed_overnight.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-09 06:00 —— 整夜补 seed：**排序在全部已补足骨干上未翻转**，效应量更强**
>
> ### 进度（22:09 启动 → 06:00，7.9 h）
>
> | 骨干 | text_only | both | vision_only |
> |---|---|---|---|
> | **CLIP B/32 @ r4** | **3/3** ✅ | **3/3** ✅ | **3/3** ✅ |
> | CLIP B/16 @ r4 | **3/3** ✅ | 2/3 | 2/3 |
> | OpenCLIP @ r4 | 1/3 | 1/3 | 1/3 |
>
> ### 结果（风险 #1 判据：最保护臂不得翻转）
>
> | 骨干 | text_only | both | vision_only | 判定 |
> |---|---|---|---|---|
> | CLIP B/32 @ r4（3 seed） | **−0.0288 ± 0.0013** | −0.0188 ± 0.0004 | +0.0127 ± 0.0024 | ✅ 未翻转 |
> | **CLIP B/16 @ r4**（3/2 seed） | **−0.0172 ± 0.0021** | +0.0139 ± 0.0016 | +0.0403 ± 0.0043 | ✅ 未翻转 |
>
> **所有两两 sd 区间均不重叠**：
> - B/32 r4：text_only vs both 差 0.0100 ≈ **7.7 倍 sd**；both vs vision 差 0.0315 ≈ **12 倍 sd**；
> - **B/16 r4：text_only vs both 差 0.0311 ≈ 14.8 倍 sd**；both vs vision 差 0.0264 ≈ 5.9 倍 sd。
>
> **→ 两处关键结论都被多 seed 加固**：
> ① **同秩对照的反例（CLIP B/16 的 text_only 最保护）不是单 run 偶然**（14.8 倍 sd）；
> ② **`vision_only` 最差**在两骨干上一致且分离明确。
>
> ### ⚠️ 一个必须修正的先前说法
>
> 我曾写"**OpenCLIP 相邻臂差异仅约 2 sd**，其排序应据此理解"。
> **那个 2 sd 是拿"单 seed 差异"除以"CLIP B/32 r8 的跨臂 sd（0.0030）"算的**——
> **参照量选错**（应逐臂 sd，实测 0.0013–0.0044）。
> **→ 待 OpenCLIP 补完 seed 后按逐臂 sd 重算**，再决定该句是否保留。
>
> ### 剩余与时间
>
> `CLIP B/16` 的 2 个臂 + `OpenCLIP` 的 9 个 run。
> 实测 `both`/`vision_only` 约 **55 min–3 h/臂** → **剩余约 6–9 h**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "整夜补 seed" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("整夜补 seed", "14.8 倍 sd", "参照量选错", "剩余约 6–9 h"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
