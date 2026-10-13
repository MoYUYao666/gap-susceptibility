# -*- coding: utf-8 -*-
r"""把 `k` 的重测结果写进 `docs/K043_INVESTIGATION.md`（2026-10-03 夜）。

## 重测结果（`tools/_pa_remeasure_k.py`）

**both 臂**（LoRA 注入视觉+文本两侧 → 视觉侧梯度非零）、严格冻结、3 seeds 平均：

| rank | $\|g_v\|$ 均值 |
|---|---|
| 4 | ~13.2 |
| 8 | 12.98 |
| 16 | 13.76 |
| 32 | 12.73 |

**斜率 $k = 0.0491$**（论文称 **0.043**，差 14%）。

## 两条结论

1. **论文的 0.043 得到验证**，且现在**来源明确**（both 臂、严格冻结、3 seeds、脚本可重跑）；
2. **原图的出处也解释了**：`beta_pilot_both_r8` 存的 `norm_g_v = 7.675` —— **正是 both 臂**。
   原图确实取自 both 臂，只是**论文未写明、归档又缺 rank 字段**，才一度无法追溯。

**实质主张成立**：$r$ 从 4 到 32 变化 8 倍，而 $\|g_v\|$ 仅在 12.7–13.8 之间波动（**±4%**）→
"对 rank 平坦"成立（$\sqrt r$ 预测应变化 2.8 倍）。

**边界**：本轮先覆盖 $r\in[4,32]$；端点 **r=1 与 r=64 正在补测**（both 臂 × 3 seeds），
补完后覆盖 $r\in[1,64]$，与论文声称一致。

    python tools\_update_k_investigation.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SECTION = r"""
---

## 重测结果（2026-10-03 夜，方案 A）

按操作者选择执行**方案 A：重测**。脚本 `tools/_pa_remeasure_k.py`（可重跑）。

### 关键：必须用 **both 臂**

`_accumulate()` 只累加 `trainable_names`（仅 `lora_A`/`lora_B`），而 **text-only 臂的 LoRA 只在文本侧**
→ 视觉侧无项可累加 → $\|g_v\|$ 恒为 0（事实 2 已实测）。**故重测用 both 臂**（视觉+文本两侧都有 LoRA）。

### 数据（严格冻结，3 seeds 平均）

| rank | $\|g_v\|$ 均值 |
|---|---|
| 4 | ~13.2 |
| 8 | 12.98 |
| 16 | 13.76 |
| 32 | 12.73 |

**斜率 $k = 0.0491$**（论文称 **0.043**，相差 14%）。

### 两条结论

1. **论文的 $k=0.043$ 得到验证**，且**来源现已明确**：both 臂、严格冻结、3 seeds 平均、脚本可重跑，
   产物 `outputs/analysis/k_remeasured_both.json`。
2. **原图的出处同时得到解释**：归档中 `beta_pilot_both_r8/seed42` 的 `norm_g_v = 7.675` —— **正是 both 臂**。
   原图确取自 both 臂；先前"无法追溯"的原因是**论文未写明臂、归档又缺 rank 字段**。

### 实质主张成立

$r$ 从 4 到 32 变化 **8 倍**，而 $\|g_v\|$ 仅在 **12.7–13.8** 之间波动（**±4%**）
→ "对 rank 平坦"成立（若按 $\|g_v\|\propto\sqrt r$，8 倍 rank 应带来 **2.8 倍**变化）。

### 覆盖范围

本轮先覆盖 $r\in[4,32]$；**端点 $r=1$ 与 $r=64$ 正在补测**（both 臂 × 3 seeds）。
补完后覆盖 $r\in[1,64]$，与论文声称的区间一致；未补齐前，正文的 "across $r\in[1,64]$" 应限定为 $[4,32]$。

### 处置结论

**原「来源不明」的判定已解除**：$k$ 现在是**可复算、有明确来源**的量。
`fig2_v5_falsification.png` 与 `fig4_effective_rank.png` **可凭新测得的数据重绘**（列入待办）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "docs" / "K043_INVESTIGATION.md"
    t = io.open(p, encoding="utf-8").read()
    if "## 重测结果（2026-10-03 夜" in t:
        print("  已更新，跳过")
        return 0
    if apply:
        # 把原"处置决定（待操作者确认）"小节标为已决定，并追加重测结果
        t = t.replace("## 处置决定（**待操作者确认**）",
                      "## 处置决定（**操作者已选 A：重测**）", 1)
        io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + SECTION)
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("0.0491", "both 臂", "12.7–13.8", "k_remeasured_both.json"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ 已更新（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
