# -*- coding: utf-8 -*-
r"""落账：实验 A 收束——**α 预测的问题仍未回答，且我已停止继续尝试**（2026-10-08 20:20）。

    python tools\_docs_a_conclusion.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🏁 2026-10-08 20:20 —— 实验 A 收束：**α 预测仍未获答案，我停止继续尝试**（第 6 次后）**
>
> ### 最后一次完整运行的实测结果（batch 64、5000 样本、10 epoch、lr 1e-4）
>
> **`inner` 终于有真实值**（四层 bug 全修掉后），但**逐 epoch 波动极大**：
>
> | epoch | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
> |---|---|---|---|---|---|---|---|---|---|---|
> | `inner` | −2.56 | −1.98 | −2.47 | **−5.61** | −2.04 | **+5.69** | **−6.81** | **+12.45** | −3.12 | −1.98 |
>
> 均值 ≈ **−0.47** → `α̂ = −η̄·mean(inner) ≈ +4.6e-5`（**符号方向正确**：`DG*` 确实在降 1.88 → 1.24）
>
> **但 `DG*` 跨度 = 0.6371，归档为 0.1641（3.9 倍）→ 未对齐 → 按事先判据不产出 α 结论。**
>
> ### 超参扫描已无方向（**且继续调就是拟合目标值**）
>
> | 配置 | DG\\* 跨度 | 相对归档 0.1641 |
> |---|---|---|
> | batch 64，3 ep，2000 样本 | 0.0817 | 0.5× |
> | batch 64，**10 ep，5000 样本** | **0.637** | **3.9×** |
> | batch 128，3 ep，5000 样本 | 0.0478 | 0.3× |
> | batch 128，10 ep，5000 样本 | 0.0478（实测） | 0.3× |
>
> **跨度对 batch 的响应与对 epoch 数的响应相互矛盾**（batch 增大 → 跨度骤降；
> epoch 增多 → 跨度骤增），**故无法用单一超参把跨度调到目标值**。
>
> **⚠️ 关键判断**：若继续调参直到跨度命中 0.1641，**那就是把自由参数拟合到检验目标上**——
> **会毁掉这个检验的意义**。**故我停止，不调了。**
>
> ### 六次尝试的完整记录
>
> | 次 | 失败原因 |
> |---|---|
> | 1 | 样本量 2000 vs 归档 5000（跨度差 15 倍） |
> | 2 | 自写训练循环（步数 780 vs 归档 630） |
> | 3 | 缺 `_trainable_params` 等属性；`clip_model` 回退到 HF 仓库 ID → 卡下载 |
> | 4 | 起点/跨度差 4 倍；`inner=nan` |
> | 5 | **CUDA OOM**（梯度版 8 批 × 图叠加，21 GiB） |
> | 6 | `inner` 修好、有真实值，但**跨度仍 3.9 倍** |
>
> ### 结论（如实写入文档，不改论文）
>
> - **梯度流恒等式本身已被直接验证**（cos = 0.9977、中位相对误差 = 0.027，
>   `outputs/theory/gradflow_identity/identity_check.json`）；
> - **但"α 能否由梯度预测"仍未回答**——本阶段 6 次尝试均未在**与归档可比的动力学**下完成测量；
> - **论文无需改动**：正文已写明 *"α and β fitted to each trajectory, not predicted from its gradients"*，
>   **从未声称 α 可预测**。故 A 是**加分项，不是承重项**。
>
> ### 我这一阶段的失误模式（第 18 次自错，同一类）
>
> **六次尝试里，前五次都是"跑起来才发现实验搭错了"。** 我每次只修一层，
> **没有在第一次就用"与归档逐项对齐"的清单做前置核对**（步数、batch、样本量、初始化、
> 调度器、梯度时机、显存）。若第一次就逐项核对，这一项**最多两次就能定论**。
> **→ 对策⑤（新增）：设计对照实验时，先写"与目标数据的逐项对齐清单"并全部核对通过，再开跑。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "实验 A 收束" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("实验 A 收束", "+12.45", "会毁掉这个检验的意义", "加分项，不是承重项",
              "对策⑤"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0N." not in m:
        add = """
**0N. 🏁 实验 A 收束：α 预测仍未获答案（2026-10-08 20:20，6 次尝试后停止）**

- **`inner` 已修好**（四层 bug：`zero_grad` 时机 → `_trainable_params`=None → 长度判据 → None 相乘 → 再加 CUDA OOM），**有真实值**：−6.8 ~ +12.5，均值 ≈ −0.47，**符号方向正确**。
- **但 `DG*` 跨度 0.6371 vs 归档 0.1641（3.9 倍）→ 按事先判据不产出结论。**
- **超参扫描无方向**（batch 64/10ep→3.9×；batch 128→0.3×；跨度对 batch 与 epoch 的响应相互矛盾）→ **继续调就是把自由参数拟合到检验目标上，会毁掉检验** → **停止**。
- **论文无需改动**：正文已写明「α、β 为逐 run 拟合，非由梯度预测」，**从未声称 α 可预测** → 加分项。
- 证据：`outputs/_alpha_A_full2.log`、`outputs/theory/alpha_trainer_based/`、`tools/_p21_alpha_trainer_based.py`。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
