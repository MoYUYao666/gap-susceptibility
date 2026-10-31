# -*- coding: utf-8 -*-
r"""记录 2026-10-03 下午阶段：理论章节修正 + α_pred 复算 + 今晚实验（阶段收尾三件套）。

    python tools\_docs_20261003_pm.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **🔧 2026-10-03 下午 —— 修理论章节的被否定声称 + 复算 α_pred + 启动今晚实验**
>
> ### ① `theory.tex` 两处仍称 "lower LoRA rank preserves alignment better"（**已修**）
>
> rank sweep 反证该规则后，扫描发现**理论章节还留着它**：
> - `theory.tex:102`：机制解释称 "the net effect favors restoration（**β increases moderately with
>   rank**）" —— **与自家 `tab:phase2` 数据相反**（text-only β：r8 **0.167** → r16 0.140 → r32
>   **0.119**，**递减**）。且严格冻结下 rank 越高间隙压得越低，与 β 更小**方向一致**。
> - `theory.tex:4`：动机陈述 "why does lower LoRA rank provide better protection" —— 前提已被否定。
> - `validation.tex:84`：**循环解释**（用 Effective Rank Saturation 反过来解释被退役的结论）。
>
> **改法**：机制改为"rank 效应经由恢复系数 β"（与数据同向）；动机句去掉被否定的前提；
> 循环句改为陈述 ERS **确实支持**的部分（$\|g_v\|$ 平坦 ⇒ 任何 rank 依赖必须来自 β）。
> 脚本 `tools/_pa_fix_theory_rank.py`、`_pa_fix_ers_circular.py`。
>
> ### ② α_pred 复算（**论文声称成立，且实测更紧**）
>
> 脚本 `tools/_pa_verify_alpha_pred.py` 按 $\alpha_{\text{pred}} = -\eta\sum_m \Gamma_m\|g_m\|$ 逐条复算
> `outputs/theory/beta_pilot/**/beta_results.json`：
>
> - **α_pred 全部为负** ✅（理论定义即带负号，`theory.tex:77`）
> - **|α_pred − α_obs| 最大 0.0026、中位 0.00099** → 论文称 "within 0.03" **成立且宽裕一个数量级**
> - ⚠️ 存储的 `alpha_estimated` **只有幅值**（无符号）→ 附录"sign agrees"应说明**符号来自定义**，
>   而非独立测量；另论文称 "six pilot configurations"，实测 **8 条记录**。
>
> ### ③ $k = 0.043$ —— **确认无法从归档复算**
>
> 含 `norm_g_v` 的记录 **329 条，无一带 rank** → 该斜率**确实重建不了**。
> 论文称曲线覆盖 $r\in[1,64]$，而现有训练只到 rank 32 → **缺 rank 1、2、64**。
>
> ### ④ 今晚启动的实验（作业 `pwsh-72`，16:53 启动）
>
> 操作者原选"跨骨干 rank sweep（4）+ CLIP vision_only + rank1"，**核实后更正两处**：
>
> - **CLIP 的 vision_only 在 rank 8 已有 5 seeds**（`outputs/strict_freeze/vision_only/`，
>   ΔCG +0.0049…+0.0164）→ 重跑浪费，换成 k 曲线缺的点；
> - **SigLIP 无 `--rank`**，rank 由配置决定；既有 `s3_siglip_lora_r4` 是 **both 位置 + legacy 约定**
>   （n_trainable=175,102,466）→ **不能替代**，已新增 `s7_siglip_lora_r4_{text_only,both}`。
>
> | 实验 | 目的 | 产物 |
> |---|---|---|
> | SigLIP r4 text_only / both | **跨骨干 rank sweep**：检验方向反转是否跨骨干成立 | `outputs/siglip_strict/seed*/s7_siglip_lora_r4_*/` |
> | OpenCLIP r4 text_only + both | 同上 | `outputs/strict_freeze_openclip_rank/r4/` |
> | CLIP r1 text_only | **补 k 曲线起点** | `outputs/strict_freeze_rank/r1/` |
> | CLIP r64 text_only | **补 k 曲线终点** | `outputs/strict_freeze_rank/r64/` |
>
> 协议：5000 样本 / 10 epochs / 严格冻结 / alpha = rank×2 ｜ seeds：SigLIP 与 OpenCLIP 用 5 个，CLIP 两点用 3 个。
> **预计约 4–5 小时**。脚本 `tools/_run_tonight_6.py`。
>
> ### ⑤ 编译状态
>
> NC 版 **41 页**、Springer 版 **31 页**、均 **0 错误 / 0 未定义引用**。投稿包待实验后一并重建。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    F = REPO / "HANDOFF.md"
    t = io.open(F, encoding="utf-8").read()
    if "2026-10-03 下午 —— 修理论章节" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **✅ 2026-10-03 —— 补充实验 38/38"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("theory.tex:102", "0.0026", "pwsh-72", "s7_siglip_lora_r4"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
