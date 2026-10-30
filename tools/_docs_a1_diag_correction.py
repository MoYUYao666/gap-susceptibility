# -*- coding: utf-8 -*-
r"""落账：更正我对 A1 的诊断（2026-10-10）。

    python tools\_docs_a1_diag_correction.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-10 —— 更正：我此前对 A1 的诊断**基本是错的**（A1 的实验面已经充分）**
>
> ### 我先前说（错）
>
> *"A1 需要补 **R2.2 top-k 消融** 与 **R2.3 更多细粒度基准**（~3–5 h）"*
>
> ### 实测（`tools/_p93_a1_topk_status.py`）
>
> | 审稿人要求 | **实际状态** |
> |---|---|
> | **R2.2** top-k 消融 | ✅ **已完成且已写入论文**：新节 `sec:topk`，**$k\\in\\{1,3,5,10,20,50,100\\}$**，同一 5000 图样本、同一扰动流，$\\rho$ 全程 **0.9125–0.9357**；产物 `outputs/a1_rr_e2_topk.json`（62 KB，`meta.experiment = "E2 top-k ablation (reviewer R2.2)"`） |
> | **R2.3** 更多零样本基准 | ✅ **论文已报 5 个**：ImageNet / Flickr30k / COCO / DTD / Food-101 / iNat |
> | **R2.5** "相关系数恰为 1.0 可疑" | ✅ 论文已**主动自我保留**：*"a **self-consistency check** of the closed form, **not independent validation**"*，并给出 `max_abs_diff 0.0019` |
> | **R1.4** 自家结果矛盾（$\\tau{=}0.615$ 却 78.6%） | ✅ 已写成 **"necessary but not sufficient"**，且**主动划出适用域** |
>
> ### → 结论修正
>
> **A1 的问题不是"实验不足"，而是"实验已经足够、且比审稿人要求的更克制"。**
> 所以**新增实验不会解决"significance 不足"**——这条编辑意见只能靠**重新定位**解决。
>
> ### 我的新判断（供操作者决定，不再猜机制）
>
> A1 里**已经埋着一个强得多的卖点，但被放在后面**：
>
> > *"$\\tau$ is an earlier and more sensitive indicator of order erosion than top-1 itself, and it is
> > computable from the top-$k$ class sets already available during validation --- making it a
> > **zero-overhead training-time monitor** for classification-oriented adaptation."*
>
> **"零开销训练期监控器"是一个可用的方法学贡献**；而当前标题
> （*"The Modality Gap Is Not a Universal Health Metric"*）是**否定式**，
> 读者的第一印象是"又一篇说某指标不好的论文"。
>
> **→ 可能的解法（三选一，须操作者定）**：
>
> | 选项 | 做法 |
> |---|---|
> | **A** | **改标题与摘要**，把"τ 作为零开销训练期监控器"提到最前；"不是普适指标"降为**支撑论据** |
> | **B** | **保留标题，改投 scope 更贴的刊**（IVC / CVIU，而非 ESWA/KBS 这类宽口径 AI 刊） |
> | **C** | **合稿**：把 A1 的"适用边界"与 `paper合` 的"何时有效"合成一篇（**风险**：两篇都在投，需谨慎披露） |
>
> ### ⚠️ 我不再给"补实验"的建议
>
> 因为实测表明**该补的已经补了**。**若我先前那条建议被执行，会白花 3–5 小时且不解决问题。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "更正：我此前对 A1 的诊断" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("更正：我此前对 A1 的诊断", "0.9125", "zero-overhead training-time monitor",
              "不会解决\"significance 不足\"", "白花 3–5 小时"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
