# -*- coding: utf-8 -*-
r"""落账：COCO 逐配置数据（27/36）+ 关键发现（2026-10-08 16:35）。

    python tools\_docs_coco_finding.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔑 2026-10-08 16:35 —— COCO 补跑 27/36：**`both` 在 COCO 上最保护**（与 Flickr30k 相反）**
>
> ### 逐配置实测（严格冻结，5000 样本 × 10 epoch，3 seed）
>
> | 配置 | seed | CGΔ 均值 | sd | R@1 |
> |---|---|---|---|---|
> | `both r=1` | 3/3 | **−0.0320** | 0.0054 | 0.121 |
> | `both r=2` | 3/3 | −0.0563 | 0.0036 | 0.120 |
> | `both r=4` | 3/3 | −0.0886 | 0.0026 | 0.120 |
> | `both r=16` | 3/3 | −0.1527 | 0.0061 | 0.119 |
> | `both r=32` | 3/3 | −0.1562 | 0.0018 | 0.120 |
> | `both r=64` | 3/3 | −0.1531 | 0.0040 | 0.122 |
> | `text_only r=4` | 3/3 | −0.0414 | 0.0015 | 0.115 |
> | `text_only r=16` | 3/3 | −0.0914 | 0.0046 | 0.114 |
> | `text_only r=64` | 3/3 | −0.1377 | 0.0021 | 0.113 |
>
> ### 🔑 关键发现：**最保护臂在 COCO 上是 `both`，在 Flickr30k 上是 `text_only`**
>
> | 秩 | Flickr30k（归档） | **COCO（新补跑）** |
> |---|---|---|
> | r=8 | text_only **−0.0465** vs both −0.0258 → **text_only** | — |
> | r=4 | text_only **−0.0297** vs both −0.0186 → **text_only** | text_only −0.0414 vs both **−0.0886** → **both** |
> | r=64 | both **+0.0305**（归档） | text_only −0.1377 vs both **−0.1531** → **both** |
>
> **→ 两个数据集上最保护臂相反。**
>
> ### 这对论文意味着什么
>
> 论文现有表述：*"the ordering is stable within an architecture, but which end of it is preferable is not."*
> —— **本条现在有了新的、独立的证据**：**不仅跨骨干不同，跨数据集也不同**。
>
> **⚠️ 暂不写入论文**，理由（按唯一原则）：
> 1. `text_only` 臂还差 **r=1、r=2、r=32**（3 个秩 × 3 seed = 9 run）才能两臂齐备全表；
> 2. 现有 COCO 数字**尚未进入正文**（正文的 COCO 表是旧的 3 行，其值为 `coco_*` 归档）；
> 3. **须先确认新旧口径可比**（旧归档 `n_trainable=145,170,177` **非严格冻结**，新补跑为严格冻结）。
>
> ### 值得注意的两处细节
>
> - **`text_only` 的 R@1 一致地低于 `both`**（0.113–0.115 vs 0.119–0.122）→ 与 Flickr30k 上
>   "最小化 gap 的臂检索最差"一致，但此处 **gap 最小的是 both**，故这一关系在 COCO 上不成立；
> - **rank 效应非单调**：`text_only` 随 rank 单调更负（−0.041 → −0.092 → −0.138），
>   而 `both` 在 r=16/32/64 趋于平台（−0.153 ~ −0.156）。
>
> ### 剩余
>
> `text_only` 的 **r=1、r=2、r=32** → **9 run ≈ 5 h**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "COCO 补跑 27/36" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO 补跑 27/36", "最保护臂在 COCO 上是 `both`",
              "暂不写入论文", "145,170,177"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
