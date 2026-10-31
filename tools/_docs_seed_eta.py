# -*- coding: utf-8 -*-
r"""落账：续跑进度 + **时间估算的第 N 次修正**（2026-10-09 10:05）。

    python tools\_docs_seed_eta.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⏱️ 2026-10-09 10:05 —— 续跑进度 + **时间估算的第 N 次修正**（规律已明确）**
>
> ### 进度（08:52 续跑 → 10:03）
>
> | 骨干 | text_only | both | vision_only |
> |---|---|---|---|
> | CLIP B/32 r4 | 3/3 ✅ | 3/3 ✅ | 3/3 ✅ |
> | CLIP B/16 r4 | 3/3 ✅ | **2/3（跑中 71 min）** | 2/3 |
> | OpenCLIP r4 | 1/3 | 1/3 | 1/3 |
>
> **跳过逻辑验证成功**：续跑时 4 个已完成的 `(骨干, 臂)` 各用 **8–9 s** 跳过（只做增量）。
>
> ### ⚠️ 时间估算规律（**多次偏乐观后终于量化**）
>
> | 臂 | 实测单 run 用时 |
> |---|---|
> | `text_only` | **约 10 min** |
> | `both` | **约 55 min – 3 h** |
> | `vision_only` | 约 30 min – 1 h |
>
> **根因**：可训张量数不同（`text_only` 392、`both` 650、`vision_only` 258）
> **且反传路径长度不同**——`both` 要同时更新两侧，图最大。
>
> **→ 修正后的估时规则（写入文档，供以后复用）**：
> **严格冻结 run 按"`both` 3 h"估，不按"`text_only` 10 min"估。**
> 本队列剩 **14 个缺口** × 平均约 1–3 h → **实际 15–40 h**（我先前说 6–9 h，**又偏乐观**）。
>
> ### 已串联的下一步
>
> 驱动跑完会自动接 **完整 `Γ_m` 测量**（`tools/_p58_gamma_clip.py`，~10 min），
> 之后按操作者选的 A **定 `Γ_m` 口径**。
>
> ### 说明
>
> **这是长跑任务，不需人工干预。** 本条目记录"估时修正"，以免日后又按乐观数字排计划。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "时间估算规律（**多次偏乐观后终于量化**）" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("时间估算规律", "按\"`both` 3 h\"估", "实际 15–40 h", "跳过逻辑验证成功"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
