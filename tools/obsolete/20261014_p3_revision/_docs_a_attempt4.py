# -*- coding: utf-8 -*-
r"""落账：实验 A 第 4 次尝试仍未对齐 + COCO 已启动（2026-10-08 10:55）。

    python tools\_docs_a_attempt4.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⚠️ 2026-10-08 10:55 —— 实验 A 第 4 次尝试仍未对齐（**如实记录，不因结论不利而省略**）**
>
> ### A 的四次尝试全表
>
> | 次 | 做法 | 结果 | 失败原因 |
> |---|---|---|---|
> | 1 | 自写循环，2000 样本 | `passed=False` | DG\\* 跨度 0.0102 vs 归档 0.1538（**差 15 倍**） |
> | 2 | 自写循环，5000 样本 | `passed=False` | 跨度 0.0159 vs 0.1641（**差 10 倍**）；`final_step` 780 vs 630 |
> | 3 | **trainer 基座**（CPU 预检通过） | **跑不起来** | 缺 `_trainable_params` 属性；`clip_model` 未给本地路径 → 卡 HF 下载 |
> | **4** | **trainer 基座**（属性补齐） | **`aligned=False`** | **四个新问题（见下）** |
>
> ### 第 4 次的实测数据（`outputs/theory/alpha_trainer_based/alpha_trainer_based.json`）
>
> | 指标 | 本次 | 归档 | 判定 |
> |---|---|---|---|
> | `total_steps` | **630** | 630 | ✅ **一致** |
> | **起始 DG\\*** | **1.88** | **1.48** | ❌ **差 0.40** |
> | **DG\\* 跨度** | **0.6389** | **0.1641** | ❌ **4 倍** |
> | lr 末值 | **0.00e+00** | ? | ❌ cosine 归零 |
> | `inner` | **全 NaN** | — | ❌ 未取得有效内积 |
>
> 逐 epoch DG\\*：`[1.88, 1.7949, 1.7158, 1.6049, 1.4799, 1.3996, 1.3317, 1.2821, 1.251, 1.2411]`
> 逐 epoch lr：`[9.8e-05, 9.0e-05, 7.9e-05, 6.5e-05, 5.0e-05, 3.5e-05, 2.1e-05, 9.5e-06, 2.4e-06, 0.0e+00]`
>
> ### 四个独立问题（都已定位，不是"没测出来"而是"没搭对"）
>
> | # | 问题 | 证据 / 推断 |
> |---|---|---|
> | 1 | **起始 DG\\* = 1.88 vs 归档 1.48** | 同 rank 8、同 batch 64、同 5000 样本、同 630 步，起点仍差 0.40 → **数据划分或 LoRA 初始化不同**（`LoRAConfig.use_gap_init` 默认 **False**，故不是 gap-init 差异） |
> | 2 | **lr 末值归零** | `CosineAnnealingLR(T_max=630)` 走到最后一步 → **训练在末期停止推进** |
> | 3 | **跨度 4 倍** | 起点高 0.40 + 早期 lr 大 → 漂移过量 |
> | 4 | **`inner` 全 NaN** | `capture_inner` 从 `p.grad` 取训练梯度，但**我在 `_train_epoch` 之外调用**，取的梯度与 `∇DG*` **不是同一模型状态**；且 epoch 末 `p.grad` 可能已被清空/含 NaN |
>
> ### 我的判断（诚实）
>
> **A 目前给不出"α 能否由梯度预测"的答案。** 需要先修四处：
> ① 用**同一模型状态**计算 `∇L` 与 `∇DG*`（而非"训练梯度 vs epoch 末 DG 梯度"）；
> ② 起始 DG\\* 对齐（排查数据划分）；
> ③ lr 调度与归档一致（归档无 lr 记录，需从其 `final_train_loss` 反推）；
> ④ 排查 NaN 来源。
>
> **这是第 4 次，且每次都暴露不同层面的问题**（样本量 → 循环实现 → 属性缺失 → 梯度状态不匹配）。
> **共同点仍是：我按"看起来对"搭实验，再发现与目标不对齐。**
>
> ### ✅ 与此同时：**COCO 补跑已正常启动**（36 h 队列）
>
> ```
> [10:35:56] ▶ COCO both r=4  日志 COCO_both_r_4.log
> Epoch 5:   2%|▎  | 2/40 [00:02<00:49, 1.29s/it, loss=0.5773]
> GPU: 7556 MiB, 100%
> ```
> **40 步/epoch**（5000/batch128），**12 配置 × 3 seed = 36 run**，可续跑。
> **此前的 `--seeds` 未拆分 bug 已修**（那次 12 个任务全部 rc=2 空转）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "实验 A 第 4 次尝试仍未对齐" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("第 4 次尝试仍未对齐", "1.88", "0.6389", "inner` 全 NaN", "COCO 补跑已正常启动"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    MARK = "0G. ⚠️ 实验 A 第 4 次尝试仍未对齐"
    if MARK not in m:
        add = """
**0G. ⚠️ 实验 A 第 4 次尝试仍未对齐（2026-10-08 10:55）—— 尚未回答中心论断**

- 四次尝试：① 2000 样本（跨度差 15 倍）→ ② 自写循环 5000 样本（差 10 倍）→ ③ trainer 基座跑不起来（缺属性、HF 下载卡住）→ **④ trainer 基座 `aligned=False`**。
- 第 4 次实测：`total_steps=630` ✅ 与归档一致；但**起始 DG\\* 1.88 vs 归档 1.48**、**跨度 0.6389 vs 0.1641（4 倍）**、**lr 末值归零**、**`inner` 全 NaN**。
- **结论：A 目前给不出"α 能否由梯度预测"的答案。** 需修四处（同一模型状态取 ∇L 与 ∇DG\\*、起始 DG\\* 对齐、lr 调度、NaN 来源）。
- 证据：`outputs/theory/alpha_trainer_based/alpha_trainer_based.json`（含 `diagnosis` 字段）、`tools/_p21_alpha_trainer_based.py`。
- **论文现状不受影响**：正文已如实写明"α、β 为逐 run 拟合，梯度流恒等式已单独直接验证"，未声称 α 可预测。

**0H. ✅ COCO 补跑已启动（36 h 可续跑）**

- `10:35:56 ▶ COCO both r=4`，实测 **40 步/epoch**、GPU 7556 MiB/100%。
- 12 配置 × 3 seed = 36 run；`--seeds` 未拆分的 bug 已修（此前 12 任务全 rc=2 空转）。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        m3 = io.open(mp, encoding="utf-8").read()
        assert MARK in m3 and "0H." in m3
        print(f"  ✅ 文件地图.md 已更新（{len(m3.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
