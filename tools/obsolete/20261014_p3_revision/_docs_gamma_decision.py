# -*- coding: utf-8 -*-
r"""落账：`Γ_m` 口径待定（等完整测量）+ 队列安排（2026-10-08 22:20）。

    python tools\_docs_gamma_decision.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⏳ 2026-10-08 22:20 —— `Γ_m` 口径**待定**（操作者选 A：等完整测量）**
>
> ### 操作者决定
>
> **等 `Γ_m` 的完整量（含 `cos φ_m`）测完再定论文口径**——
> 因为**若完整量能预测而范数不能，则现在改口径就会把对的改成错的**。
>
> ### 待测项（`tools/_p58_gamma_clip.py`，已写好）
>
> CLIP B/32 三臂的**完整** `Γ_m = ‖∇_mDG*‖·cos φ_m`（8 批平均，含 cos），
> 与实测 `CGΔ` 对照；据此判断：
>
> | 结果 | 论文处置 |
> |---|---|
> | 完整 `Γ_m` **能**预测最优位置 | **保留**"初始化即可算出"的表述 |
> | 完整 `Γ_m` **不能**预测 | **统一为"机制量"**，把 `introduction:13` 与 `discussion:26` 的预测性措辞降级为待验证扩展 |
>
> ### 队列安排（GPU 串行）
>
> | 序 | 任务 | 状态 | 预估 |
> |---|---|---|---|
> | 1 | **补 seed**（3 骨干 × 3 臂 × 2 seed = 18 run） | ▶ **跑中** | ~4–5 h |
> | 2 | **完整 `Γ_m`（CLIP 三臂）** | 待 GPU | ~10 min |
> | 3 | 依 #2 结果决定 `Γ_m` 口径 | 待定 | — |
>
> ### 本轮已完成的风险项
>
> | # | 风险 | 状态 |
> |---|---|---|
> | **#2** | `Γ_m` 在解码器 VLM 上验证 | ✅ **完成**（硬校验通过：冻结侧梯度严格为 0） |
> | **#5** | 用 `Γ_m` 替代 `α` 预测 | ✅ **完成**（得到跨架构不对称：文本侧梯度差 127 倍；**完整量待补测**） |
> | **#1** | 补 seed | ▶ **跑中** |
> | **#3** | OpenCLIP 效应量最弱（~2 sd） | 由 #1 的补 seed **一并解决**（同一骨干补 2 seed） |
> | **#4** | COCO 缺的 `text_only` 3 个秩 | 待办（~5 h） |
> | **#6** | 训练规模小 | 已标注"测排序非最终精度"，**不补** |
>
> ### 一处已确认的论文张力（待 #2 结果后处置）
>
> `introduction.tex:13` 说 `Γ_m` *"requiring only the computation of $\\Gamma_m$ at initialization"*，
> `discussion.tex:6` 说 *"The question is **not** whether $\\Gamma_m$ is a 'good' predictor"*。
> **两者口径不一致，须在 #2 结果出来后统一。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "`Γ_m` 口径**待定**" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("口径**待定**", "把对的改成错的", "18 run", "统一为\"机制量\""):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
