# -*- coding: utf-8 -*-
r"""记录：把 95 个严格冻结对照计入实验目录与全文计数（2026-10-05，操作者提出）。

    python tools\_docs_add_sf_to_counts.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **🔢 2026-10-05 —— 实验计数更正：补上未计入的 95 个严格冻结对照（**操作者提出**）**
>
> 操作者问："**实验数量有变化呀，我们不是跑了可多实验吗**" —— **确实少报了。**
>
> ### 问题
>
> | 计数 | 内容 | 是否含严格冻结 |
> |---|---|---|
> | 117 | Part I 的机理实验（13 类） | ❌ |
> | 162 | ODE 拟合验证 | ❌ |
> | 278 | 117 + 162 | ❌ |
> | **95** | **严格冻结对照** | **完全未计入** |
>
> **而严格冻结对照正是本稿核心主张（适配位置效应）的唯一可靠依据**——
> legacy 约定下 text-only 臂实际训练约 1.45 亿参数，**并未隔离"适配位置"**。
> 即：论文**把最强证据放在了计数之外**，且**少报了自己的实验量**。
>
> ### 盘点（`tools/_count_strictfreeze_runs.py`，从 `outputs/` 实测）
>
> | 组 | run |
> |---|---|
> | CLIP r8 三臂 | 15 |
> | CLIP rank sweep r1/4/16/32/64 | 30 |
> | OpenCLIP r8 三臂 | 15 |
> | OpenCLIP r4 两臂 | 10 |
> | SigLIP r8 text_only/both | 10 |
> | SigLIP r8 vision_only | 5 |
> | SigLIP r4 两臂 | 10 |
> | **合计** | **95**（CLIP 45 / OpenCLIP 25 / SigLIP 25） |
>
> ### 更正（10 处，脚本 `tools/_pa_add_strictfreeze_to_catalog.py`）
>
> - **附录目录表**：新增第 **XIV 类 "Strict-Freezing Controls (three backbones, $r\in[1,64]$)" = 95**，
>   **Total 117 → 374**；
> - 表注 "thirteen sections" → **fourteen sections**；
> - 附录正文首句改为列出三段构成（117 机理 + 162 ODE + 95 严格冻结），并说明
>   **"最后一组正是位置效应结论所依赖的"**；
> - 正文各处（`introduction` ×2、`empirical` ×2、`conclusion` ×2、`validation` ×1）：
>   **117 / 278 → 374**。
>
> **核验**：残留 `117 experiments` = **0**、`278 experiments` = **0**；`374` 出现 9 处（另 1 处
> `empirical.tex` 的 `0.374` 是梯度范数数值，**经核实未误改**）。
> NC **42 页**、Springer **31 页**、0 错误。
>
> ### 教训
>
> 我在同日早些的"投稿前审核"里**没查实验计数**——只查了"已写数字是否被数据支撑"，
> **没问"实验做了这么多，数字是否还是旧的"**。这条是**操作者发现**的。
> 已把计数盘点固化为脚本，便于日后新增实验后重跑。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "实验计数更正：补上未计入的 95 个严格冻结对照" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **🔎 2026-10-05 —— Paper A 投稿前审核"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("95", "374", "fourteen sections", "操作者提出"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
