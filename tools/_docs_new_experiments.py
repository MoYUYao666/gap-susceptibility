# -*- coding: utf-8 -*-
r"""记录优先级 1 与优先级 2 的实验结果（2026-10-05）。

    python tools\_docs_new_experiments.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

REPORT = r"""# 补充实验报告：理论根基与机制的**直接**验证

> 日期：**2026-10-05** ｜ 依据：`tools/_exp1_gradflow_identity.py`、
> `tools/_exp2b_mechanism_gradient_interference.py`、`tools/_exp2c_encoder_side_gradients.py`
> 产物：`outputs/theory/gradflow_identity/`、`outputs/theory/grad_interference/`、
> `outputs/theory/encoder_side/`、`outputs/theory/gap_direction/`

## 为什么做这两项

论文的两大支柱此前都是**间接**验证：

| 支柱 | 此前的验证 | 缺口 |
|---|---|---|
| ODE 从**梯度流恒等式**推出 | 轨迹拟合 $R^2 = 0.986$ | **拟合好 ≠ 推导对** |
| "视觉侧干预有害" | 框架**预测** | **机制从未直接测量** |

## 实验一：梯度流恒等式**直接**验证 ✅

$$\Delta DG^* \;\overset{?}{=}\; -\eta\,\langle \nabla_\theta DG^*,\ \nabla_\theta \mathcal{L}\rangle$$

**做法**：同一次构造下取两套梯度，再做**一个真实 SGD 步**，比较预测与实测。
（关键：$DG^*$ 在**含 L2 归一化的计算图内**求导，不 detach。）

| 位置 | seed | 预测 | 实测 | 比值 |
|---|---|---|---|---|
| text_only | 42 / 123 / 456 | −1.98e−4 / −8.55e−4 / −2.85e−4 | −1.87e−4 / −8.64e−4 / −2.53e−4 | 0.95 / 1.01 / 0.89 |
| both | 42 / 123 / 456 | −6.56e−4 / −6.02e−4 / −3.23e−4 | −6.65e−4 / −5.79e−4 / −3.28e−4 | 1.01 / 0.96 / 1.02 |
| vision_only | 42 / 123 / 456 | −2.34e−4 / −3.39e−4 / −4.53e−4 | −2.45e−4 / −3.30e−4 / −4.64e−4 | 1.05 / 0.97 / 1.02 |

**$\cos(\text{预测},\text{实测}) = 0.9977$ ｜ 中位相对误差 $= 2.70\%$**

**判据（事先写明：$\cos>0.9$ 且相对误差 $<20\%$）→ 远超通过。**

**意义**：ODE 的推导前提**不再只是"拟合得像"，而是被直接验证**。

## 实验二：按编码器侧分解梯度 ✅ **理论预测全部成立**

| 位置 | $\|\nabla_{\theta_v} DG^*\|$ | $\|\nabla_{\theta_t} DG^*\|$ | $\|g_v\|$ | $\|g_t\|$ |
|---|---|---|---|---|
| **text_only** | **0.0000** | 1.5162 | **0.0000** | 13.5077 |
| both | 1.7613 | 1.6025 | 12.9289 | 11.0456 |
| **vision_only** | 1.8599 | **0.0000** | 15.4371 | **0.0000** |

**理论预测（逐位置）**：

| 预测 | 结果 |
|---|---|
| `text_only` → $g_v = 0$ | ✅ **精确成立**（0.0000） |
| `vision_only` → $g_t = 0$ | ✅ **精确成立**（0.0000） |
| `both` → 两侧非零 | ✅ 成立 |

**→ 论文最核心的理论断言（"文本侧适配消除视觉梯度项"）得到直接验证。**

### 机制图景（数据支持）

| 位置 | 视觉侧扰动压力 |
|---|---|
| vision_only | $g_v = 15.44$，**仅视觉侧** → 最大 |
| both | $g_v = 12.93$ 且 $g_t = 11.05$ → 中等 |
| text_only | $g_v = 0$ → **无视觉侧扰动** |

**与三臂实测排序一致**：$\Delta$CG 为 text_only **−0.0465** < both −0.0258 < vision_only **+0.0106**。

## 实验三（附加）：间隙方向的秩 1 程度

| 量 | 值 |
|---|---|
| $\|\overline{z^I - z^T}\|$ | 0.8076 |
| $\text{mean}\|z_i^I - z_i^T\|^2$ | 1.3677 |
| **沿 $\hat d$ 的解释方差占比** | **0.4820** |
| 中心化后第一奇异值占总能量 | 0.2691 |

**判据（>0.5）→ 0.4820，未达** → **CLIP ViT-B/32 上间隙不完全是单一方向**。

**与 `sharma2026readout`（CLIP/SigLIP 上 94.4–99.9%）的关系**：他们的量是
"**图像-文本均值分离**的平方范数被单一方向解释的比例"，
本文此处是"**逐对差向量**沿均值方向的能量占比"——**两者口径不同，不可直接比较**。
**已如实标注口径差异**，不作"矛盾"表述。

## 对稿件的意义（**待操作者决定是否写入**）

| 发现 | 可加强的主张 | 建议位置 |
|---|---|---|
| 恒等式直接验证（cos 0.998） | **ODE 的理论根基** | §Theory 末 或 §Validation 首 |
| $g_v = 0$ 逐位置精确成立 | **核心理论断言** | §Theory "The text-only position" |
| 编码器侧梯度表 | **机制解释**（不只现象） | §Validation 新小段 + 可选小表 |
| 间隙方向非严格秩 1 | **如实边界** | §Discussion 局限 |

## 复核入口

```powershell
python tools\_exp1_gradflow_identity.py --apply
python tools\_exp2b_mechanism_gradient_interference.py --apply
python tools\_exp2c_encoder_side_gradients.py --apply
python tools\_exp2_mechanism_gap_direction.py --apply
```
"""

ENTRY = r"""> **🧪 2026-10-05 晚 —— 补充实验：理论根基与机制获**直接**验证**
>
> 操作者问"**还有什么实验可以补充，对观点有利的**"。按要求先盘点薄弱处，再做**优先级 1 + 2**
> （都不需新模型/新训练，几小时量级）。报告：`docs/NEW_EXPERIMENTS_20261005.md`。
>
> ### 缺口（为什么值得补）
>
> | 支柱 | 此前验证 | 缺口 |
> |---|---|---|
> | ODE 从**梯度流恒等式**推出 | 轨迹拟合 $R^2=0.986$ | **拟合好 ≠ 推导对** |
> | "视觉侧干预有害" | 框架**预测** | **机制从未直接测量** |
>
> ### 实验一：恒等式**直接**验证 ✅
>
> $$\Delta DG^* \overset{?}{=} -\eta\langle\nabla_\theta DG^*, \nabla_\theta\mathcal{L}\rangle$$
>
> 同一次构造取两套梯度 + **一个真实 SGD 步**。（关键：$DG^*$ 在**含 L2 归一化的图内**求导。）
>
> **9 个配置（3 位置 × 3 seeds）全部通过**：
> $$\cos(\text{预测},\text{实测}) = \mathbf{0.9977}\quad\text{中位相对误差} = \mathbf{2.70\%}$$
>
> 判据（事先写明 $\cos>0.9$、误差 $<20\%$）**远超**。
> 产物 `outputs/theory/gradflow_identity/identity_check.json`。
>
> ### 实验二：按编码器侧分解梯度 ✅ **理论预测逐位置全部成立**
>
> | 位置 | $\|g_v\|$ | $\|g_t\|$ | 理论预测 | 结果 |
> |---|---|---|---|---|
> | **text_only** | **0.0000** | 13.5077 | $g_v=0$ | ✅ **精确成立** |
> | both | 12.9289 | 11.0456 | 两侧非零 | ✅ |
> | **vision_only** | 15.4371 | **0.0000** | $g_t=0$ | ✅ **精确成立** |
>
> **→ 论文最核心的理论断言（"文本侧适配消除视觉梯度项"）获得直接验证。**
>
> 机制图景：视觉侧扰动压力 vision_only(15.44) > both(12.93) > text_only(**0**)，
> **与三臂实测 ΔCG 排序一致**（−0.0465 < −0.0258 < +0.0106）。
> 产物 `outputs/theory/encoder_side/encoder_side.json`。
>
> ### 附加：间隙方向的秩 1 程度（**如实记录，未达判据**）
>
> 沿均值方向的解释方差占比 **0.4820**（判据 >0.5 **未达**）→ **CLIP B/32 上间隙非单一方向**。
> 与 `sharma2026readout`（94.4–99.9%）**口径不同**（他们量均值分离的平方范数被单一方向解释的比例；
> 此处量逐对差向量沿均值方向的能量占比），**不作矛盾表述**。
>
> ### 对稿件的意义（**是否写入待操作者决定**）
>
> | 发现 | 可加强 | 建议位置 |
> |---|---|---|
> | 恒等式直接验证 | ODE **理论根基** | §Theory 末 或 §Validation 首 |
> | $g_v=0$ 精确成立 | **核心理论断言** | §Theory "The text-only position" |
> | 编码器侧梯度表 | **机制解释**（不只现象） | §Validation 新小段 |
> | 非严格秩 1 | **如实边界** | §Discussion 局限 |
>
> ### 顺带记录：本阶段踩的两个坑（避免重犯）
>
> 1. **臆测接口名**：我先写了 `build_dataloaders` / `inject_lora`，**两者都不存在**；
>    正确是 `create_dataloaders` / `apply_lora_to_model`。**教训：动手前先查签名**（本次靠先查躲过了白跑）。
> 2. **`lora_state_dict` 结构**：实为 `{base_name: {'A':…, 'B':…}}`，**不是** `.lora_A.weight` 键名；
>    且我最初设计的"$\Delta W$ 与间隙方向外积对齐度"**对随机矩阵期望值也是 $\sim1/\sqrt{\text{in}}$**，
>    **没有区分度**——故改为有明确零假设的 $\cos(\nabla DG^*,\nabla\mathcal L)$。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    rp = REPO / "docs" / "NEW_EXPERIMENTS_20261005.md"
    io.open(rp, "w", encoding="utf-8", newline="").write(REPORT)
    t = io.open(rp, encoding="utf-8").read()
    for k in ("0.9977", "2.70", "0.0000", "13.5077", "15.4371", "0.4820"):
        assert k in t, f"报告断言失败：缺 {k}"
    print(f"  ✅ 报告已写出 docs/{rp.name}（{len(t.splitlines())} 行）")

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "补充实验：理论根基与机制获" not in h:
        anchor = "> **🗂️ 2026-10-05 —— ap3 已无可投路径"
        i = h.find(anchor)
        if i < 0:
            print("  ⚠ 未找到 HANDOFF 锚点")
            return 1
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENTRY + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("0.9977", "g_v=0", "直接验证", "NEW_EXPERIMENTS_20261005"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
