# -*- coding: utf-8 -*-
r"""落账：实验 A 就绪 + 同秩对照入队 + 两个方法论修正（2026-10-08 08:00）。

    python tools\_docs_a_ready.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🧪 2026-10-08 08:00 —— 实验 A 就绪（trainer 基座）+ 同秩对照入队 + 两处方法论修正**
>
> ### 实验 A 的做法（**操作者选 A**）
>
> **不再自己写训练循环**，改为**子类化 `GapAwareTrainer`**，复用它的 `_train_epoch` 与
> `CosineAnnealingLR(T_max=len(loader)×epochs)` → **训练动力学必然与归档一致**。
> 只在每 epoch 末尾加**一次额外反向**测 `⟨∇_θDG*, ∇_θL⟩`：
>
> 1. 取本 epoch 的损失梯度 `g_L`；2. 设 `loss = DG*(val)` 反向得 `g_dg`；
> 3. `inner = ⟨g_dg, g_L⟩`；4. 预测 `α̂ = −η̄·mean(inner)`。
>
> **脚本**：`tools/_p21_alpha_trainer_based.py`
> **判据（事先写明）**：`corr>0.7` 且 中位相对误差 `<35%` 且 比值 `∈[0.5,2]`。
>
> ### 🔴 两处方法论修正（**都是我自己写错，都是实测抓出**）
>
> | # | 错误 | 更正 |
> |---|---|---|
> | 1 | **把 ODE 拟合的量当成质心间隙 `cg`** | 论文拟合的是 **`dg_star`（配对均方距离 `(1/N)Σ‖z_I−z_T‖²`）**。归档里 `dg_star` 跨度 **0.1641** vs `cg` **0.1149**——**是两个不同的量**。我的梯度必须按 `src/dg_star_tracker.py:compute` 的确切定义算。 |
> | 2 | **同秩对照缺失** | 论文 patch-32 组是 **rank 8**，我新增的 CLIP B/16 是 **rank 4** → **不同秩，无法把"排序由 patch size 决定"与"由预训练目标决定"区分**。**已入队补 `CLIP B/32 @ rank 4`（三臂）**。 |
>
> ### 队列已扩展（18 项）
>
> **新插入**（在 ③b 之后、COCO 之前——便于尽早拿到结论）：
> - `同秩对照 CLIP B/32 r4 both`
> - `同秩对照 CLIP B/32 r4 text_only`
> - `同秩对照 CLIP B/32 r4 vision_only`
>
> ⚠️ **正在运行的执行器实例用的是启动时构建的旧队列**（`build_queue()` 在开头调用一次）。
> **计划**：等 ③b `vision_only` 跑完（约 18 min）→ **重启执行器**（会拾取含新对照的队列）。
>
> ### 为什么同秩对照是决定性的
>
> 已有证据：
>
> | 骨干 | patch | 预训练 | 最保护臂 |
> |---|---|---|---|
> | CLIP B/32 (WIT) | 32 | WIT | text_only |
> | OpenCLIP B/32 (LAION) | 32 | LAION | text_only |
> | SigLIP B/16 | 16 | **WebLI（sigmoid 目标）** | both |
> | BioCLIP B/16 | 16 | **生物域** | both |
> | **CLIP B/16 (WIT)** | **16** | **WIT（与 B/32 同目标）** | **text_only** |
>
> **观察**：两个 patch-16 骨干恰好都是**非 WIT 预训练**；而唯一 WIT 的 patch-16 给出的是 patch-32 的排序。
> **→ 假说：排序跟的是**预训练目标/语料**，不是 patch size。**
> **同秩 CLIP B/32 r4 的作用**：排除"rank 4 本身导致 text_only 更保护"这一替代解释。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "实验 A 就绪（trainer 基座）" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("实验 A 就绪", "配对均方距离", "同秩对照缺失", "预训练目标/语料", "18 项"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
