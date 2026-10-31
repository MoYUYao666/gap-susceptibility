# -*- coding: utf-8 -*-
r"""落账：队列实测速度与修正后的完成时间（2026-10-10 晚）。

    python tools\_docs_eta.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⏱️ 2026-10-10 22:03 —— 队列进度 14/46 + **时间估计上调**（操作者："就照常跑完"）**
>
> ### 一、进度（22:03，队列已跑 128 分钟）
>
> | 阶段 | 状态 |
> |---|---|
> | **P1 OCLIP r4（12 run）** | ✅ **全部完成**（335–401 s/run） |
> | P2 B/16 r4 | ▶ `text_only` 补 2 seed（**698 s / 672 s**）｜`vision_only/seed456` 重跑中 |
> | P3 COCO text_only（19 run） | 排队 |
> | P4 B/32 r4（6 run） | 排队 |
>
> **14/46 完成，0 失败**｜GPU 99%，8.0/8.2 GB（满负荷）
>
> ### 二、实测单 run 耗时（用于修正估计）
>
> | 组 ／ 臂 | 实测 |
> |---|---|
> | OCLIP r4 三臂 | 335–401 s（~6 min） |
> | **B/16 r4 `text_only`** | **~11 min** |
> | **B/16 r4 `vision_only` / `both`** | **~1.9 h** ← **瓶颈** |
>
> ### 三、修正后的完成时间
>
> | 阶段 | run | 预计 |
> |---|---|---|
> | B/16 剩余（`vision_only`×2 + `both`×3，各 ~1.9 h） | 6 | **~11.5 h** |
> | COCO text_only（~10 min/run） | 19 | ~3.2 h |
> | B/32 r4 | 6 | ~1.5 h |
> | **合计** | 31 | **~16 h** |
>
> **→ 原估"次日 10:00"上调为"次日约 14:00–15:00"**；之后接 VLM 13-seed（~48 min）。
>
> ### 四、为什么慢（**物理限制，非 bug**）
>
> ViT-B/16 在 8 GB 卡上算力吃紧：`vision_only`/`both` 的 run 里视觉塔全部可训练，
> 单 run 1.9 h。**这是硬件约束**，与批次修正无关。
>
> ### 五、操作者决定
>
> > **"就照常跑完"**（即选项 A：批次统一是关键正确性问题，慢也得跑完）
>
> **不降优先级、不牺牲 B/16 的 5 seed 目标。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "时间估计上调" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("时间估计上调", "14/46", "698 s / 672 s", "14:00–15:00", "就照常跑完"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
