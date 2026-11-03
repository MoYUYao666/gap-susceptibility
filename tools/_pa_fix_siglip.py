# -*- coding: utf-8 -*-
r"""Paper A 整改 · 补全 SigLIP 段（数值已核实；协议性质需如实标注）。

## 核实结果（数值全对，但协议有性质问题）

`outputs/siglip/` 的 run 与正文数值**精确对应**：

| run | cg_init | cg_final | CGΔ | 正文 |
|---|---|---|---|---|
| `s4_siglip_lora_text_only` | 1.07422 | 1.14156 | **+0.0673** | +0.067 ✅ |
| `s4_siglip_lora_both` | 1.07383 | 1.13222 | **+0.0584** | +0.058 ✅ |
| `s1_siglip_frozen` | 1.07446 | —（参照） | — | — |

**但协议性质需标注**：这两个 run 的可训参数为 **189,276,674**（text-only）与 **175,397,378**（both）
——**又是 legacy 冻结约定**（`src/lora.py:215-236` 从不冻结基座；`get_peft_params` 返回全部
`requires_grad` 参数）。所以"text-only 优于 both"在 SigLIP 上**同样不可解读为"位置选择"的证据**：

> text-only 反而训练了**更多**参数（189M > 175M）——它只是不额外注入视觉侧 LoRA。

同一签名在多个架构上重复（BLIP-2：两者同为 196,672,514；CLIP：145M vs 131M），
说明这是**该库 LoRA 实现的跨模型性质**，不是单一架构的偶然。

## 处置

**不跑 SigLIP 严格冻结实验**（评估后决定）：
- `experiments/strict_freeze_control.py` 深度耦合 CLIP（`CLIPModel`/`CLIPProcessor`、
  `model.vision_model.encoder.layers`）；SigLIP 适配器结构不同，改造为架构级工作；
- 且需重跑 15 次全量训练（5 seeds × 3 配置），CLIP 上单次约 350 s，SigLIP 更大；
- **收益有限**：正文已把主张范围收窄，SigLIP 本就是"附加架构"证据；
- 已在规格文档记为**可选后续实验**。

→ 本脚本改为**如实标注协议性质**，并把数值核对结果写进注释与规格。

    python tools\_pa_fix_siglip.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

OLD = ("The gap-level predictions of the framework extend to additional architectures and PEFT methods "
       "measured in Section~\\ref{sec:empirical}: on SigLIP the text-only arm changes CG by $+0.067$ against "
       "$+0.058$ for the both-position arm, and on Adapter the corresponding figures are $+0.064$ and "
       "$+0.058$ at $d{=}64$.")

NEW = ("The gap-level predictions of the framework extend to additional architectures and PEFT methods "
       "measured in Section~\\ref{sec:empirical}: on SigLIP the text-only arm changes CG by $+0.067$ against "
       "$+0.058$ for the both-position arm, and on Adapter the corresponding figures are $+0.064$ and "
       "$+0.058$ at $d{=}64$. Both sets of runs come from the earlier adaptation convention, in which the "
       "LoRA backbone was not frozen: the SigLIP text-only arm trained $1.89\\times10^{8}$ parameters "
       "against $1.75\\times10^{8}$ for the both-position arm, so as with the CLIP comparison in "
       "Section~\\ref{sec:empirical} these two arms do not isolate a choice about which encoder to touch. "
       "Their gap values remain reported because they are measured, but they carry no claim about the "
       "text-only advantage for those architectures; establishing that on SigLIP requires the strict-freezing "
       "control used for CLIP.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if OLD not in t:
        print("  ⚠ 未命中；当前该段：")
        i = t.find("The gap-level predictions")
        print("    " + (t[i:i + 420].replace("\n", " ") if i >= 0 else "（未找到）"))
        return 1
    print("  ✅ 命中 SigLIP/Adapter 段")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "do not isolate a choice" in t2, "断言失败：未写入协议披露"
        assert "strict-freezing" in t2, "断言失败：未写入所需对照"
        print("  ✅ 已改并断言通过（数值保留 + 协议性质如实披露）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
