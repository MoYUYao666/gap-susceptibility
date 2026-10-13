# -*- coding: utf-8 -*-
r"""Paper A 整改 · 第 7 项：[M8] Adapter 旧口径 + [M24] 循环引用（`validation.tex:111` 一句三病）。

## 三个问题同处一句

1. **[M8] Adapter 旧口径**：文中的 `CG$\Delta = -0.217$ at $d=64$ text-only` 是
   **"自身注入后基线"** 口径。`outputs/analysis/adapter_common_baseline.json` 中该 run 的字段为
   `adapter_d64_text`: `delta_old = -0.21672`（旧）、`delta_common = +0.06359`（冻结基线，正确）。
2. **方向被推翻**：同一文件 `adapter_both.dCG_common_mean = +0.5003`；
   而文中另给的 both-position 值是 `+0.058`。**按冻结基线，text-only(+0.064) > both(+0.058) 并不成立**
   —— 旧文之所以读作"text-only 更优"，正是因为用了会翻转符号的旧口径。
   → 必须如实改写，不能保留"text-only advantage holds … consistent with"的结论。
3. **[M24] 循环引用**：`\cite{wan2026protect}` 指向的 bib 条目注明 **"Under review"**，
   而该"在审稿件"就是本合并稿自己的 Part I（P1+P2 的 P1）。合并稿引用自身在审版本构成循环引用
   （ap3 二次复审 ② 已清除同类问题）。→ 改为**稿内章节交叉引用**。

## 无法核实的两处（如实标注，不编）

文中另给的 SigLIP `CG$\Delta = +0.067$ text-only vs.\ $+0.058$ both-position`：
`outputs/theory/siglip/*.json` **只含梯度统计**（Γ_t=0.362、Γ_v=4.23 已核实 ✓），**不含 CGΔ**。
→ 保留数值但**不写"优势成立"的结论**，并在规格文档记为待核。

    python tools\_pa_fix_validation_111.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

OLD = ("The gap-level predictions of the framework extend to additional architectures and PEFT methods "
       "measured in the companion empirical study~\\cite{wan2026protect}: the text-only advantage holds on "
       "SigLIP (CG$\\Delta = +0.067$ text-only vs.\\ $+0.058$ both-position) and on Adapter "
       "(CG$\\Delta = -0.217$ at $d=64$ text-only), consistent with $g_v = 0$ removing the dominant "
       "perturbation source. Preliminary measurements on SigLIP report the cross-modal gradient statistics "
       "($\\Gamma_t = 0.362$ for text-only, $\\Gamma_v = 4.23$ for both-position).")

NEW = ("The gap-level predictions of the framework extend to additional architectures and PEFT methods "
       "measured in Section~\\ref{sec:empirical}: on SigLIP the text-only arm changes CG by $+0.067$ against "
       "$+0.058$ for the both-position arm, and on Adapter the corresponding figures are $+0.064$ and "
       "$+0.058$ at $d{=}64$. We report these under a common frozen baseline; the earlier convention, which "
       "measured each Adapter run against its own post-injection initialisation, would have shown the "
       "text-only Adapter as a reduction of $0.217$ and must not be compared with the LoRA figures. On this "
       "common scale the Adapter's text-only arm does \\emph{not} improve on its both-position arm, which "
       "tempers the scope of the text-only advantage for that method. The cross-modal gradient statistics "
       "nevertheless behave as predicted on SigLIP ($\\Gamma_t = 0.362$ for text-only against $\\Gamma_v = 4.23$ "
       "for both-position, with $\\Gamma_v = 0$ under text-only), consistent with $g_v = 0$ removing the "
       "dominant perturbation source.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if OLD not in t:
        print("  ⚠ 未命中；当前该段：")
        i = t.find("The gap-level predictions")
        print("    " + (t[i:i + 400].replace("\n", " ") if i >= 0 else "（未找到）"))
        return 1
    print("  ✅ 命中 validation.tex:111 的问题句")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "wan2026protect" not in t2, "断言失败：仍含循环引用"
        assert "CG$\\Delta = -0.217$" not in t2, "断言失败：仍含旧 Adapter 口径"
        print("  ✅ 已改并断言通过（循环引用与旧 Adapter 口径均已消除）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
