# -*- coding: utf-8 -*-
r"""Paper A 整改 · 补漏：`theory.tex:98` 仍含两个旧值（noise 2.6× 与 gradient 1.5×）。

## 判定（逐处核实后）

全文 "1.5"/"2.6" 共 7 处，其中 **6 处是合法数字**，只有 `theory.tex:98` 是错的：

| 位置 | 内容 | 判定 |
|---|---|---|
| `empirical.tex:19` | 零样本 mean **2.6%**（准确率） | ✅ 合法 |
| `empirical.tex:113` | 零样本 mean **2.6%** | ✅ 合法 |
| `empirical.tex:103` | 引述"旧探针曾称 **2.6×**" | ✅ 合法（撤回说明需要引述） |
| `supplement.tex:50` | 图注引述 **2.6×** 并标为已撤回 | ✅ 合法 |
| `theory.tex:100` | 零样本崩到 **2.6%** | ✅ 合法 |
| **`theory.tex:98`** | **"noise sensitivity $2.6\times$ greater, gradient contribution $1.5\times$"** | ❌ **错**：噪声线已撤回；GSNR 实测为 **1.411** |

## 改法

不只改数字，而是**改掉对已撤回结论的依赖**：因果链改为落在"移除视觉梯度项"上
（$g_v=0$，严格冻结下有直接证据），与 §empirical 的最终口径一致。

    python tools\_pa_fix_theory_stale.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "theory.tex"

OLD = ("Section~\\ref{sec:empirical} showed that vision encoders exhibit higher sensitivity to perturbation "
       "(noise sensitivity $2.6\\times$ greater, gradient contribution $1.5\\times$). This higher sensitivity "
       "manifests as larger $\\bar{\\Gamma}_v$, making $\\alpha_{\\text{both}}$ more positive---i.e., more "
       "gap-expanding---than $\\alpha_{\\text{text}}$.")
NEW = ("Section~\\ref{sec:empirical} shows what the second term costs: under joint-modality training the vision "
       "encoder receives the larger gradient signal ($1.41\\times$ the text encoder's norm in the reference "
       "measurement), whereas under strict freezing a text-only arm registers no vision-side update at all. "
       "The perturbation force under joint training therefore carries a term that text-only training removes "
       "entirely, which makes $\\alpha_{\\text{both}}$ more positive---i.e., more gap-expanding---than "
       "$\\alpha_{\\text{text}}$.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if OLD not in t:
        print("  ⚠ 未命中；当前该句：")
        i = t.find("showed that vision encoders")
        print("    " + (t[max(0, i - 60):i + 300].replace("\n", " ") if i >= 0 else "（未找到）"))
        return 1
    print("  ✅ 命中 theory.tex:98 的旧句")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "noise sensitivity $2.6\\times$ greater" not in t2, "断言失败：仍含旧噪声主张"
        assert "gradient contribution $1.5\\times$" not in t2, "断言失败：仍含 1.5×"
        assert "1.41" in t2, "断言失败：未写入 1.41"
        print("  ✅ 已改并断言通过")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
