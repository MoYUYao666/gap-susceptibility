# -*- coding: utf-8 -*-
r"""落账：实验 ⑥（非自然图像域零样本外部效度）完成（2026-10-07）。

    python tools\_docs_exp6_zs.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **🧪 2026-10-07 深夜 —— 实验 ⑥（非自然图像域零样本外部效度）：**方向支持，但幅度极小****
>
> 脚本：`tools/_p5_nonnatural_zs.py`（v1，**用错定义**）、`_p5_nonnatural_zs2.py`（v2，采信）。
> 输出：`outputs/analysis/nonnatural_zs_check2.json`。**零 GPU**（纯分析）。
>
> ### 第一版用错了"保护"的定义（自我修正）
>
> v1 把"gap 保持"定义为 **|CGΔ| 最小** → 得"最保护臂 = Vision-only"（|Δ|=0.0106），
> 据此判"零样本最优臂 ≠ gap 最优臂（**0/4**）"。
>
> **但这与论文定义相反**。论文的"保护"（*Protect, Don't Perturb*）指 **CGΔ 最负（gap 收窄）**：
>
> | 臂 | CGΔ | 按"收窄最多" | 按"\|Δ\| 最小" |
> |---|---|---|---|
> | **Text-only** | **−0.0465** | **1（最保护）** | 3 |
> | Both | −0.0258 | 2 | 2 |
> | Vision-only | **+0.0106** | 3（**反向**） | 1 |
>
> **两种定义给出相反的最优臂** → v1 结论无效。v2 按论文定义重做。
>
> ### v2 结果（Flickr30k 微调 → DTD / Food101 零样本，相对 frozen 的百分点变化）
>
> | 条件 | Text-only | Both | 零样本最优 | 与最保护臂(Text-only) |
> |---|---|---|---|---|
> | `dtd_food101_zs_check` / DTD | +0.43 | +0.16 | Both | ❌ |
> | 同上 / Food101 | −0.74 | −0.69 | Both | ❌ |
> | `zeroshot_extra` / DTD | +0.06 | −0.74 | **Text-only** | ✅ |
> | 同上 / Food101 | +0.07 | −0.87 | **Text-only** | ✅ |
>
> **一致 3/4**；排序在 4 个条件中 2 种 → **方向支持、不稳定**。
>
> ### ⚠️ 两条必须如实标注的局限
>
> 1. **幅度极小**：所有条件的变化**都在 ±0.9 个百分点内**（论文自己的表述是"stays within 0.8 pp"）。
>    **差异在这个量级上不宜解读为有意义的排序**——它支持"各臂零样本都几乎不掉"，
>    **但不足以断言"gap 小的臂零样本更好"**。
> 2. **Vision-only 数据缺失**：零样本只测了 2 臂（Text-only / Both），
>    **无 vision_only** → **无法检验"gap 变宽是否导致零样本更差"**，
>    而这一条恰是"gap 作健康信号"最有力的检验方向。**需补测 vision_only 的零样本**。
>
> ### 对论文的意义
>
> **不需改动**：论文对零样本的表述本就是"各臂保持在 0.8 pp 内"（保守、正确）。
> 本实验**支持该保守表述**，并**否决**了把它加强为"gap 小的臂零样本明确更好"的可能。
> **若日后要补 `vision_only` 零样本**，成本约 **0.5 h GPU**（同协议三数据集）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "实验 ⑥（非自然图像域零样本外部效度）" in h:
        print("  已记录，跳过")
        return 0
    anchor = "> **📐 2026-10-07 深夜 —— 待跑实验设计落盘"
    i = h.find(anchor)
    assert i > 0, "未找到 HANDOFF 锚点"
    io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENT + "\n" + h[i:])
    h2 = io.open(hp, encoding="utf-8").read()
    for k in ("用错了", "3/4", "幅度极小", "Vision-only 数据缺失", "非自然图像域零样本"):
        assert k in h2, f"HANDOFF 断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
