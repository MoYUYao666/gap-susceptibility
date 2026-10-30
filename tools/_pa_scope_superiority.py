# -*- coding: utf-8 -*-
r"""给四处 "text-only superiority" 加范围限定（2026-10-02）。

## 冲突的性质（必须如实说明，不是措辞问题）

- **理论**（`theory.tex:98`）：$g_v=0 \Rightarrow \alpha_{\text{text}} = -\eta\bar\Gamma_t\|g_t\|$，
  而 $\alpha_{\text{both}} = -\eta(\bar\Gamma_v\|g_v\| + \bar\Gamma_t\|g_t\|)$，
  且实测 $\|g_v\| > \|g_t\|$（1.41×）→ **预测 $\alpha_{\text{text}}$ 更优**。
- **实测**（严格冻结，同预算同 seeds 同 rank）：
  CLIP text_only 更降间隙（t=+10.0）；**SigLIP both 更降间隙（t=−52.7）**。

→ 冲突的根源是**范围**：ODE 在**给定**扰动分配下预测轨迹；它**不预测分配本身**。
当某架构的优化把更多视觉侧扰动分配到 both 臂时，该臂可能反而更降间隙。
这不是"理论错了"，而是"理论的作用域是给定分配的轨迹，不是分配方向"。

## 改法（4 处，逐处不同）

1. `introduction.tex:15`：标签改为"位置效应"，并点明方向的经验依赖性由 §validation 给出；
2. `theory.tex:98`：标题改为不含"superiority"的表述 + 段末加范围声明；
3. `validation.tex:117`：补"该预测在 CLIP 上成立、在 SigLIP 上不成立"；
4. `conclusion.tex:7`：同 1。

    python tools\_pa_scope_superiority.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS: list[tuple[str, str, str, str]] = [
    ("introduction.tex",
     "The ODE explains the empirical regularities as consequences rather than observations. Text-only "
     "superiority follows from $g_v = 0$: removing the dominant visual perturbation term leaves only the "
     "weaker text contribution.",
     "The ODE explains the empirical regularities as consequences rather than observations. For a given "
     "allocation of perturbation, the text-only position follows from $g_v = 0$: removing the dominant "
     "visual term leaves only the weaker text contribution. Whether that position is in fact the better "
     "one is a separate, empirical matter, and Section~\\ref{sec:validation} shows it depends on the "
     "architecture.",
     "introduction:15 加范围限定"),
    ("theory.tex",
     "\\textbf{Text-only superiority.} When only the text encoder is trained, the visual task gradient "
     "vanishes: $g_v = 0$.",
     "\\textbf{The text-only position.} When only the text encoder is trained, the visual task gradient "
     "vanishes: $g_v = 0$.",
     "theory:98 标题去 superiority"),
    ("validation.tex",
     "\\item \\textbf{Text-only superiority:} $g_v = 0$ eliminates the dominant visual perturbation term in "
     "$\\alpha = -\\eta\\sum_m \\bar{\\Gamma}_m\\|g_m\\|$. Text-only $\\alpha$ is consistently more "
     "negative than both-position $\\alpha$ for all ranks.",
     "\\item \\textbf{The text-only position:} $g_v = 0$ eliminates the dominant visual perturbation term in "
     "$\\alpha = -\\eta\\sum_m \\bar{\\Gamma}_m\\|g_m\\|$. On CLIP, text-only $\\alpha$ is consistently more "
     "negative than both-position $\\alpha$ for all ranks, and the strict-freezing control confirms that "
     "ordering on the measured gap. The control on SigLIP does \\emph{not}: there the both-position arm "
     "reduces the gap while the text-only arm increases it. The ODE is not falsified by this, because it "
     "predicts trajectories for a \\emph{given} allocation of perturbation rather than predicting which "
     "allocation an optimiser will find; what it does not supply is a rule for the latter, which is why the "
     "direction has to be measured per architecture.",
     "validation:117 补 CLIP 成立 / SigLIP 不成立 + 作用域说明"),
    ("conclusion.tex",
     "This ODE provides a unified explanation for the empirical regularities: text-only superiority follows "
     "from $g_v = 0$ removing the dominant perturbation source;",
     "This ODE provides a unified explanation for the empirical regularities: the text-only position "
     "follows from $g_v = 0$ removing the dominant perturbation source for a given allocation;",
     "conclusion:7 加给定分配限定"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for fname, old, new, why in EDITS:
        p = S / fname
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        else:
            print(f"  ⚠ {fname}: 未命中（{why}），出现 {c} 次")
    print(f"\n{n}/{len(EDITS)} 处{'已改' if apply else '可改'}")
    if apply:
        t = io.open(S / "validation.tex", encoding="utf-8").read()
        assert "not falsified by this" in t, "断言失败：作用域说明未写入"
        assert "does \\emph{not}" in t, "断言失败：SigLIP 反例未写入"
        left = 0
        for f in list(S.glob("*.tex")) + [REPO / "paper合" / "main_springer.tex"]:
            left += io.open(f, encoding="utf-8").read().count("text-only superiority")
        print(f"  ✅ 断言通过；全文 'text-only superiority' 残留 {left} 处（应为 0）")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
