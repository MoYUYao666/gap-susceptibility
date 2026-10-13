# -*- coding: utf-8 -*-
r"""记录 `k = 0.043` 的调查结论（2026-10-03）。

## 操作者的标准

> **所有数据必须真实来源明确，不确定的可以重跑，不确定的删除。**

`k = 0.043` 是全文**唯一**未能满足该标准的数字，故单独成档。

## 调查到的四条事实（**每条都可复核**）

| # | 事实 | 证据 |
|---|---|---|
| 1 | **无法从归档复算** | 含 `norm_g_v` 的记录 **329 条，无一带 rank**（`tools/_pa_recompute_k.py` 的清单）；rank sweep 的 `results.json` **不含**该字段 |
| 2 | **text-only 臂的 $\|g_v\|$ 在构造上恒为 0** | `src/gap_susceptibility.py` 的 `_accumulate()` 有 `if name not in trainable_names: continue`，而 `trainable_names` 只含 `lora_A`/`lora_B`；text-only 臂的 LoRA 只在文本侧 → 视觉侧无项可累加。实测：严格冻结下 4 个 rank 全为 0.0000；legacy 约定下 5 个 rank 亦全为 0.0000 |
| 3 | **论文未写明 $\|g_v\|$ 曲线来自哪个臂** | `validation.tex:84`、`supplement.tex:77` 只说 "$\|g_v\|$ is flat across $r\in[1,64]$" |
| 4 | **归档里 `norm_g_v` 的值互不一致** | `beta_pilot_both_r8/seed42` = **7.675**；adapter 系列 = 0.978 / 0.623 / 0.881 / 0.710 / 0.294；我的复算 = 0.0000 |

## 结论

**在重测之前，`k = 0.043` 及其支撑的 Effective Rank Saturation 属于"来源不明"**，
按操作者标准**应重测或删除**。

**影响范围有限**：该结论是**次级机制声称**，**不在三条设计模式内**；删除它不影响本文的主要结论。
但 `validation.tex:84` 那句被用作两处推理的前提（"任何 rank 依赖必须经由 β"），删改时需一并处理。

## 重测配方（**必须用对臂**）

```python
# 对 both 与 vision_only 臂、每个 rank 的 checkpoint：
#   1. 载入模型（**不**调用 strict_freeze 亦可——该函数会 skip frozen 参数）
#   2. 前向取 image_embeds / text_embeds（注意不能用 no_grad，该量需要梯度）
#   3. compute_gap_susceptibility(model, image_embeds, text_embeds)["norm_g_v"]
#   4. 对 log(rank) 做最小二乘拟合
# 注意：text-only 臂不可用（恒为 0，见事实 2）
```

可用 checkpoint：
- both 臂：`outputs/strict_freeze/both/seed42/best_checkpoint.pt`（rank8）等
- vision_only 臂：`outputs/strict_freeze/vision_only/seed42/best_checkpoint.pt`（rank8）

    python tools\_write_k_investigation.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

DOC = r"""# `k = 0.043` 调查记录

> **操作者标准**（2026-10-03）：所有数据必须真实来源明确；不确定的可以重跑；不确定的删除。
> `k = 0.043` 是全文**唯一**未满足该标准的数字，故单独成档。

## 它在论文里的作用

| 位置 | 用途 |
|---|---|
| `validation.tex:84` | $\|g_v\|$ 对 rank 平坦 ⇒ **Effective Rank Saturation**，并据此推"任何 rank 依赖必须经由 $\beta$" |
| `supplement.tex:77` | `fig:falsification` 的图注：随机 rank-$r$ 投影（$R^2=0.96$）对比实际 $\|g_v\|$（$k=0.043$） |
| `fig2_v5_falsification.png`、`fig4_effective_rank.png` | 两张图的**唯一**数据来源 |

## 四条已核实的事实

| # | 事实 | 证据（可复核） |
|---|---|---|
| **1** | **无法从归档复算** | 含 `norm_g_v` 的记录 **329 条，无一带 rank**；rank sweep 的 `results.json` 不含该字段。脚本 `tools/_pa_recompute_k.py` |
| **2** | **text-only 臂的 $\|g_v\|$ 在构造上恒为 0** | `src/gap_susceptibility.py` 的 `_accumulate()`：`if name not in trainable_names: continue`，而 `trainable_names` 只含 `lora_A`/`lora_B`。text-only 的 LoRA 只在文本侧 → 视觉侧无项。**实测**：严格冻结下 rank 4/8/16/32 全为 `0.0000`；legacy 约定下 rank 4/8/16/32/64 亦全为 `0.0000` |
| **3** | **论文未写明曲线来自哪个臂** | `validation.tex:84`、`supplement.tex:77` 均只称 "flat across $r\in[1,64]$" |
| **4** | **归档里 `norm_g_v` 的值互不一致** | `beta_pilot_both_r8/seed42` = **7.675**；adapter 系列 = 0.978 / 0.623 / 0.881 / 0.710 / 0.294；本次复算 = 0.0000 |

## 结论

**在重测之前，$k = 0.043$ 与 Effective Rank Saturation 属于「来源不明」**，应重测或删除。

**影响范围有限**：这是**次级机制声称**，**不在三条设计模式内**；删掉不影响主要结论。
但 `validation.tex:84` 那句话被用作另一处推理的前提（"梯度范数平坦 ⇒ 任何 rank 依赖必须经由 $\beta$"），
删改时需一并处理，不能只删数字。

## 重测配方（**必须用对臂**）

```python
# 对 both 与 vision_only 臂、每个 rank 的 checkpoint：
#   1. 载入模型（不必调用 strict_freeze）
#   2. 前向取 image_embeds / text_embeds —— 注意**不能用 torch.no_grad()**，该量需要梯度
#   3. compute_gap_susceptibility(model, image_embeds, text_embeds)["norm_g_v"]
#   4. 对 log(rank) 做最小二乘拟合得 k
# ⚠ text-only 臂不可用：恒为 0（事实 2）
```

可用 checkpoint：`outputs/strict_freeze/both/seed42/best_checkpoint.pt`（rank8）、
`outputs/strict_freeze/vision_only/seed42/best_checkpoint.pt`（rank8），
以及 `outputs/strict_freeze_rank/{r4,r16,r32}/{both,vision_only}/seed42/` 等。

## 处置决定（**待操作者确认**）

| 选项 | 代价 | 后果 |
|---|---|---|
| **A. 重测** | 需为各 rank × {both, vision_only} 跑 `compute_gap_susceptibility`（无训练，较快） | 得到**来源明确**的 $k$；若与 0.043 不符，需按实测改写 ERS 段 |
| **B. 删除** | 改 2 处正文 + 删 2 张图 | 失去一条次级机制声称，主要结论不受影响 |
| C. 保留但标注未验证 | 最小 | **不符合操作者标准**（"不确定的删除"），不建议 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if apply:
        out = REPO / "docs" / "K043_INVESTIGATION.md"
        io.open(out, "w", encoding="utf-8", newline="").write(DOC)
        t = io.open(out, encoding="utf-8").read()
        for k in ("329 条", "trainable_names", "7.675", "text-only 臂不可用"):
            assert k in t, f"断言失败：缺 {k}"
        print(f"  ✅ 已写出 {out.relative_to(REPO)}（{len(t.splitlines())} 行）")
    else:
        print("  （预演，加 --apply 写出）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
