# -*- coding: utf-8 -*-
r"""落账：对称 lr 扫描推翻我方主张 + 稿中该段重写（2026-10-13 12:10）。

    python tools\_p481_record_matched_loss.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔻 2026-10-13 12:10 —— 对称 lr 扫描推翻我方主张：**匹配任务损失后 Γ-guided 反而更差**；稿中该段**整段重写**；AdaLoRA 如实承认更优**
>
> ### 一、对称 lr 扫描（8 run 完成，消除不对称）
>
> | 方案 | `lr` | n | **ΔE 均值** | sd | **loss_last** |
> |---|---|---|---|---|---|
> | `exp` | 5e-5 | 6 | **+1477.5** | 1563.3 | 1.3762 |
> | `uniform` | 5e-5 | 6 | **+5047.5** | 1899.9 | 1.3734 |
> | **`exp`** | **3e-4** | 2 | **+5967.8** | 4775.1 | **0.5872** |
> | **`uniform`** | **3e-4** | 2 | **+2842.1** | 876.2 | **0.5826** |
> | `exp` | 1e-3 | 2 | +2867.4 | 873.2 | 0.2402 |
> | `uniform` | 1e-3 | 2 | +4935.8 | 9083.7 | 0.2294 |
> | *AdaLoRA* | 3e-4 | 1 | **−1468.2** | — | 1.4866 |
> | *AdaLoRA* | 1e-3 | 1 | **−757.3** | — | 0.9767 |
>
> ### 二、🔴 三条结论（第二条是**对我方主张最强的反证**）
>
> 1. **"Γ-guided 优于 uniform" 随 lr 反转**：5e-5 优（+1478 vs +5048）、**3e-4 劣**（+5968 vs +2842）、
>    1e-3 优但 `uniform` **sd=9084 且跨 −1487…+11359** ⇒ **不能作为稳健主张**
> 2. **🔴 匹配任务损失后优势**消失**：3e-4 两侧 loss 匹配到 **0.5872 vs 0.5826**（差 0.8%），
>    而 **`exp` 落后（+5968 vs +2842）** ⇒ **5e-5 下的优势很可能是"训练得更少"的副产物，不是分配规则的功劳**
> 3. **AdaLoRA 对称调 lr 后仍优于全部 Γ 侧方案**（−1468.2 / −757.3 vs 最好 +1477.5）
>    ⇒ **与我的预期一致**；且 **3e-4 的 E 轨迹单调降（22003）vs 1e-3 的震荡（27331 尖峰）** ⇒ **loss 低 ≠ 能量稳**
>
> ### 三、✅ 稿中该段**整段重写**（`tools/_p480`；P3 编译 **14 页 / 0 错 / 0 未定义**）
>
> **为什么是重写而非改数字**：旧结论的**逻辑**已被推翻（"这个分配比均匀好"不再成立）。
>
> 新结构：
> - **保留** 5e-5 的 $p=0.0055$ **但立刻声明不稳健**：*"That comparison does not survive being repeated
>   at other learning rates, and we report the failure rather than the first result."*
> - **3e-4 反转**、**matched-loss 那一刀** ⇒ *"most plausibly a side-effect of training less far,
>   not a property of the allocation rule, and we therefore **no longer claim** that the rule beats
>   the uniform baseline on $\\Delta E$."*
> - **随机池 47 分位 + 3/10 更优**；**反序不显著（$p=0.21$）+ 3-seed 的 0.037 记为小样本假象**
> - **新增小节 *An adaptive baseline is better on this metric, and we say so***：
>   AdaLoRA −1468/−757 vs 我们最好 +1478；**明确"两侧同范围扫描过"（消除不对称）**；记录能量尖峰
> - **新增小节 *What the rule is for***：
>   *"The contribution of the $\\Gamma$ statistic is not that it allocates better than a search,
>   but that it allocates **without searching**"* +
>   **"Where such a search is affordable, a method like AdaLoRA should be preferred, and our results say it should."**
> - **保留** $n$ = **11–28** 的功效上限与"噪声主要来自组内"
>
> **⇒ 该叙事与稿件 Summary 的 zero-shot / cross-architecture 定位一致，审稿人无法挑刺。**
>
> ### 四、⚠️ 我核出成员终报里一处**旧数**
>
> 它终报写 *"Required n … is 20–43 per arm"* —— **那是 P2 前的数**（用 Δ=4172 与旧 σ）。
> **P2 后 Δ=3570.1、σ 更新 ⇒ 正确区间是 11–28**（**它自己在 P2 后也报了 11–28**，终报回退到旧值）。
> **已要求统一改为 11–28。** **这正是我们刚立规矩的又一次实例：数字随数据更新，旧值必须被替换而非留在别处。**
>
> ### 五、答复口径定稿（四组意见）
>
> | 意见 | 答复 |
> |---|---|
> | **R2.2** | ✅ **正面答复**：真做了逐块非均匀分配（`{4,2,2,9}` vs `{4,4,4,4}`）+ **同预算逐位对齐**；但**证据用 matched-loss 口径**，并**如实说明优势不稳健** |
> | **R2.4 / R3.9** | ✅ **如实承认 AdaLoRA 在 $\\Delta E$ 上更优**（**对称调 lr 后仍成立**）；定位收紧为"**零样本、分配决策不含目标模型梯度**" |
> | **R3.21** | ✅ **彻底解决**（57 run 实测唯一值 $7{,}237{,}632$ + 逐 run 断言） |
> | **R3.12** | ✅ **已提供**（Qwen2-VL-2B 实测逐块 $\\Gamma$ + rank 表 + CLIP/LLaVA 既有归档对照） |
>
> ### 六、状态
>
> - **task-9 实验部分收口**（成员与我一致）；GPU 已交还（299 MiB / idle）
> - **P1 ✅（30）｜P2 ✅（6 seed / 57 run）｜P3 ✅（AdaLoRA + 双侧对称 lr 扫描）**
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 25 处**
> - **PRL 硬约束**：**双栏 ≤7 页** ⇒ 待压缩 + 新建 Supplementary
> - **剩余**：① 页数压缩 ② 33 条回复信正式文本 ③ 成员改 `20–43 → 11–28`
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "匹配任务损失后 Γ-guided 反而更差" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("匹配任务损失后", "0.5872", "the adaptive method wins", "without searching", "11–28"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
