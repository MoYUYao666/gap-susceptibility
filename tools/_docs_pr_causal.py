# -*- coding: utf-8 -*-
r"""落账：PR R1.3/R2.4/R3.3 因果加固完成（task-2）（2026-10-12）。

## 结论（`tools/_p255`，426 条件，0 失败，交叉运行逐位一致）

**在匹配相对扰动预算下，vision 塔并不是更脆弱的那个。**

    python tools\_docs_pr_causal.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-12 —— PR R1.3/R2.4/R3.3 因果加固完成（task-2）：**匹配相对扰动下 vision 塔并不更脆弱****
>
> ### 交付件
>
> `docs/PR_CAUSAL_FIX.md`（含**可直接粘贴的英文段落**与 limitation 清单）｜
> `tools/_p255_relative_perturbation.py`（主实验：4 协议 × 426 条件，0 失败，`--resume` 可用，~21 min）｜
> `tools/_p256_pr_causal_tables.py`（**从 JSON 渲染全部引用表格，不手抄数字**）｜
> `tools/_p257_pr_causal_repro_check.py`（**跨运行逐位一致检查**）｜
> 归档 `outputs/analysis/pr_relative_perturbation{,_verdict,_tables.md,_repro_check}.json`
>
> **复现检查**：136 个重叠条件，**R@1/R@5/R@10/CG/DG/drop%/rel_injected 最大 |diff| = 0.000e+00**。
>
> ### 直接答案
>
> **不是。** 在**逐张量匹配相对扰动**（`‖ΔW‖_F/‖W‖_F = r`，逐块且逐塔验证到 1.4e−8）下：
>
> | 协议 | 池化降幅比 vision/text（非饱和层级） | **匹配损伤预算比**（>1 ⇒ vision 更脆弱） |
> |---|---|---|
> | **`rel_layer`** | **0.610 ± 2.283**（n=30，仅 10/30 > 1） | 5%：**0.912 ± 0.452**｜10%：**0.989 ± 0.449**｜20%：**1.061 ± 0.435** |
> | `rel_uniform` | **0.410 ± 0.285**（1/30 > 1） | 5%：0.686 ± 0.184 |
> | **`abs_std`**（归档协议 `σ·std(W_i)`） | 1.293 ± 1.424（13/29 > 1） | 10%：≈1.10｜20%：1.455 ± 0.165 |
> | `abs_raw`（等绝对 σ） | **1.507 ± 0.958**（20/30 > 1） | 5%：1.013 ± 0.203 |
>
> **匹配损伤预算比 ≈ 1 ± 0.44 → 与"无差异"不可区分。**
> 论文原先称"vision 的检索退化约为 text 的 **2.6 倍**"，而归档协议下我们实测为
> **1.293**（10% 损伤预算比 ≈ **1.10**，20% ≈ **1.46**），**不是 2.6×**。
>
> ### 审稿人前提的量化（R1.3 的"核心"）
>
> | 事实 | 值 |
> |---|---|
> | **同一 σ ⇒ 塔级相对扰动 vision 大 1.1408×**（0.483σ vs 0.424σ），**与 σ 无关** | ✅ 审稿人的直觉成立 |
> | **塔内**逐张量相对扰动跨度（σ=0.3） | **17.7×**（LayerNorm 0.098σ vs attention/MLP 1.000σ） |
> | 逐块跨度 | vision 0.0945–0.2161（2.29×）｜text 0.1076–0.1442（1.34×） |
> | 注入集规模 | vision **85,054,464** vs text **37,828,608** 参数（**2.25×**）；vision 注入集占本塔 **97.3%**，text 仅 **59.9%** |
> | **只改分配、不改预算**：vision 塔级预算固定 r=0.1，`rel_layer` → `abs_raw` 使 vision 降幅从 **14.7% 变 84.0%**（配对 Δ = **−69.28 ± 7.07**） | ✅ |
>
> ### ⚠️ 两处**方法描述的溯源错误**（须改稿）
>
> 1. 归档注入器的 "skip LayerNorm" 判据是 `'layernorm' in name.lower()`，
>    而 HF 命名为 `layer_norm1.weight` → **LayerNorm 实际被注入了**（每塔 192 张量）。
>    LayerNorm 参数占 vision 注入 Frobenius 范数的 **73.9%**（text **79.7%**）。
> 2. 噪声是 **`σ·std(W_i)` 逐张量缩放**，**不是各向同性/绝对**。
>    → `paper合/sections/empirical.tex:144` 的 *"isotropic Gaussian noise in the encoder
>    parameters"* **与代码不符**，须改为"逐张量尺度相对噪声（含 LayerNorm）"。
>
> ### Visual Fragility 的裁决
>
> **作为因果证据不成立，作为稳定的经验排序也不成立**：匹配相对预算下无可分辨的不对称
> （预算比 ≈1 ± 0.44），且**方向随协议与损伤水平翻转**。
> **仍然成立的只有严格冻结对照**（适配器放在文本侧、视觉编码器未被触碰，收益依然存在）——
> 故 "Visual Fragility" 应保留为**关于适配器放在哪里**的**假设**，而非机制结论。
>
> ### 证据
>
> `outputs/analysis/pr_relative_perturbation.json`（status=**complete**，baseline R@1 0.6950 /
> CG 0.7742 / DG 0.8308）｜`_verdict.json`｜`_tables.md`（T1–T8）｜`_repro_check.json`
>
> **待 Lead 做**：`HANDOFF.md`（本条）、`文件地图.md`、以及改稿合成。
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "因果加固完成（task-2）" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("因果加固完成（task-2）", "0.610", "0.912", "1.1408", "2.6 倍",
              "isotropic", "0.000e+00", "LayerNorm 实际被注入了"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
