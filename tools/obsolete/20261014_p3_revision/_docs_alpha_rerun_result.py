# -*- coding: utf-8 -*-
r"""落账：α 重跑结果（仍不可用）+ 根因 + 队列已自动推进（2026-10-08 04:15）。

    python tools\_docs_alpha_rerun_result.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📊 2026-10-08 04:15 —— α 重跑完成（`rc=0`）：拟合变好，但**预测仍不可用**，根因已定位**
>
> ### 结果（`max_samples=5000`，`outputs/theory/alpha_from_gradients/alpha_from_gradients.json`）
>
> | seed | α_fit | α̂(梯度) | β_fit | **R²_fit** | **α̂/α_fit** |
> |---|---|---|---|---|---|
> | 42 | −0.00202 | −0.000071 | 0.0511 | **0.866** | **0.035** |
> | 123 | −0.00352 | −0.000048 | 0.1385 | **0.827** | **0.014** |
>
> `corr = −1.0`（**只有 2 条轨迹，此值无意义**）｜中位相对误差 **0.976**｜`passed = False`
>
> **样本量 2000→5000 的效果**：`R²_fit` 从 **0.023** 升到 **0.866**（拟合可信了），
> 但 **α̂ 仍系统性偏小 30–70 倍** → **预测不成立**。
>
> ### 🔴 根因：**我的 α 脚本与归档用的不是同一套训练动力学**
>
> | 项 | 归档 `v1_both_r8` | 我的 α 脚本 |
> |---|---|---|
> | **final_step** | **630**（63 步/epoch × 10） | **780**（78 步/epoch × 10） |
> | final_train_loss | **0.0605** | （未收敛） |
> | **R@1** | **0.5999** | 远低 |
> | 调度器 | trainer 的 `CosineAnnealingLR(T_max=len(loader)×epochs)` | **脚本自己 new 的**，口径不同 |
>
> **DG\\* 跨度**：归档 **0.1641** vs 我的 **0.0159 / 0.0191** → **差 10 倍**。
> 而两者的"内积均值"都在 **1.3 量级**（相近）→ **差异在训练动力学，不在梯度量级**。
>
> **`src/config.py` 默认**：`batch_size=64, lr=1e-4, scheduler="cosine", warmup_steps=100`。
> **我的脚本自行实现了循环**（未走 trainer 的 `warmup + cosine(T_max=total_steps)`）→ **步数与调度都不一致**。
>
> ### 结论（必须分清）
>
> - ❌ **不是**"α 不能被梯度预测"（**仍未获证据**）
> - ✅ **是**"我的对照实验没有复现归档的训练条件，故测不出"
>
> **这是第二次同类错误**：先按"看起来合理"的参数搭实验，再发现与目标数据不同口径。
> **→ 新增判据（已固化）：对照实验的**动力学量**（步数、调度、最终损失）必须先与目标数据对齐，再谈预测。**
>
> ### ✅ 队列已自动推进（执行器按设计工作）
>
> ```
> [04:01:13] ✅ α重跑(5000样本): 已有任务已结束 → 复查完成判据
> [04:01:13] ⏭ α重跑(5000样本) 现已完成（合格）→ 跳过
> [04:01:13] ▶ ③b both  日志 ③b_both.log
> ```
>
> **GPU 已释放**（392 MiB / 7%）。剩余：③b `both` → ③b `vision_only` → COCO 12 配置 × 3 seed。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "预测仍不可用" in t and "0.1641" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("预测仍不可用", "0.866", "630", "warmup_steps=100", "动力学量"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
