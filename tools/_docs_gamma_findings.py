# -*- coding: utf-8 -*-
r"""落账：风险 #2 与 #5 的结果 + 一条对论文有影响的发现（2026-10-08 22:15）。

    python tools\_docs_gamma_findings.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-08 22:15 —— 风险 #2（`Γ_m` 在解码器 VLM）与 #5（改用 `Γ_m`）的结果**
>
> ### #2：`Γ_m` 可在解码器 VLM 上测出，**硬校验通过**
>
> 实测（`tools/_p54_gamma_vlm.py` → `outputs/analysis/gamma_vlm.json`，单批瞬时）：
>
> | 臂 | ‖g_vision‖ | ‖g_text‖ | cos_v | cos_t | Γ_vision | Γ_text |
> |---|---|---|---|---|---|---|
> | `text_only` | **0.0000** ✅ | 0.1061 | — | +1.0000 | 0.0000 | **+0.1061** |
> | `vision_only` | **14.5424** | **0.0000** ✅ | +1.0000 | — | **+14.5424** | 0.0000 |
> | `both` | 14.5344 | 0.1150 | +1.0000 | +0.0079 | +14.5339 | **+0.0009** |
>
> **两条预写硬校验都过**（冻结侧的 `∇DG*` 严格为 0），**与 CLIP 侧同一标准**
> （`encoder_side` 归档：`text_only` 的 `norm_g_vision = 0.0000`）。**故机制层在新架构上可测。**
>
> ### #5：一份**结构性不对称**——文本侧梯度敏感度跨架构差 127 倍
>
> | 模型 | ‖∇_tDG*‖ | ‖∇_vDG*‖ |
> |---|---|---|
> | **CLIP B/32** | **13.5077** | 15.4371 |
> | **Qwen2-VL-2B** | **0.1061** | 14.5424 |
>
> **视觉侧几乎相同（15.4 vs 14.5，差 6%），而文本侧相差 127 倍。**
> → **"文本侧适配比视觉侧更能收窄 gap"这一机制基础，在解码器 VLM 上弱得多。**
> 这与实测**一致**：Qwen 上 `text_only` 的相对降幅 73.9% 略低于 `both` 的 83.8%，
> 而 CLIP 上 `text_only` 是最保护臂。
>
> **→ 这是 `Γ_m` 的"敏感性因子"（‖∇_mDG*‖）随架构族改变的**定量证据**，须如实写入。
>
> ### ⚠️ 但仍**不得**从范数推"最优位置"（我的中间结论已自我修正）
>
> `tools/_p57` 只用**范数**（归档无 cos），得到"范数大的一侧 ≠ 效果更好"：
>
> | 模型 | 按范数预测最优侧 | 实测最优臂 |
> |---|---|---|
> | CLIP B/32 | vision_only（15.44 > 13.51） | **text_only** ❌ |
> | Qwen2-VL | vision_only（14.54 ≫ 0.106） | **both** ❌ |
>
> **但论文的 `Γ_m = ‖∇_mDG*‖·cos φ_m` 是完备量**，且进入动力学的是 **`Γ_m·‖g_m‖`**
> （`theory.tex:67`）——**只用范数推断预测力是不完整的**。
> **→ 已写 `tools/_p58_gamma_clip.py` 补测 CLIP 三臂的**完整 `Γ_m`（含 cos）**，
> 待 GPU 空出后跑**（当前补 seed 队列占用）。
>
> ### 📌 一处必须注意的论文表述（与我的数据有张力）
>
> `introduction.tex:13`：*"$\Gamma_m$ … **requiring only the computation of $\Gamma_m$ at
> initialization**"*；`discussion.tex:26`：*"enabling pre-hoc configuration selection without training"*。
>
> **而 `discussion.tex:6` 又明确写道**：*"The question is not whether $\Gamma_m$ is a 'good'
> predictor but whether the ODE it generates fits the data."*
>
> **→ 论文内部对 `Γ_m` 的定位有三种说法**（"初始化即可算出/可预先选配置" vs "不是预测器"）。
> **我的数据显示**：`Γ_m` 的**范数分量**不预测最优位置；**完整 `Γ_m` 待测**。
> **建议**：把 `introduction` 与 `discussion` 的表述**统一为"机制量"**，
> 并把"pre-hoc selection"降级为**待验证的扩展**（`discussion` 的 extensions 段已如此措辞）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "风险 #2（`Γ_m` 在解码器 VLM）与 #5" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("风险 #2（`Γ_m` 在解码器 VLM）与 #5", "13.5077", "0.1061", "相差 127 倍",
              "requiring only the computation"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
