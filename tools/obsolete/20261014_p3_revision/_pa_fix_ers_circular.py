# -*- coding: utf-8 -*-
r"""修正 Effective Rank Saturation 段里指向被退役结论的**循环解释**（2026-10-03）。

## 问题

`validation.tex:84` 结尾：

> "This explains why **lower rank preserves alignment better** (Section~empirical) and why $\alpha$ remains
> negative across all ranks---the perturbation force is bounded by $r_{\text{eff}}$ rather than configured
> $r$."

两个毛病：

1. **循环解释**：该段用 Effective Rank Saturation（$\|g_v\|$ 对 rank 平坦，$k=0.043$）**反过来解释**
   "lower rank 更好" —— 而"lower rank 更好"正是被严格冻结 rank sweep **反证**的结论；
2. **半句仍然有效**："$\alpha$ 在所有 rank 上为负"是**独立成立**的观测（`tab:phase2` 的 $\alpha$ 列），
   且与"$r_{\text{eff}}$ 而非配置 $r$ 限制扰动强度"的机制一致。

## 改法

只删掉依赖被退役结论的那半句，保留并**加强**仍然成立的部分——并说明它在新数据下**得到了更强的支持**：
若 $\|g_v\|$ 对 rank 平坦，则扰动强度不随 rank 增长，于是 rank 的效应必须来自**恢复系数 $\beta$**，
这正是新结果（rank 越高 $\beta$ 越小、间隙压得越低）所显示的方向。

    python tools\_pa_fix_ers_circular.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

OLD = ("This explains why lower rank preserves alignment better (Section~\\ref{sec:empirical}) and why "
       "$\\alpha$ remains negative across all ranks---the perturbation force is bounded by "
       "$r_{\\text{eff}}$ rather than configured $r$.")
NEW = ("This is why $\\alpha$ remains negative across all ranks---the perturbation force is bounded by "
       "$r_{\\text{eff}}$ rather than by configured $r$. It also constrains where a rank effect can come "
       "from: if the task-gradient norm is flat in $r$, the perturbation side of the ODE barely moves with "
       "rank, so any rank dependence must enter through the restoring coefficient $\\beta$. The "
       "strict-freezing sweep in Section~\\ref{sec:empirical} is consistent with that reading, with "
       "$\\beta$ falling as rank grows and the gap settling correspondingly lower.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中循环解释句")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "This explains why lower rank preserves alignment better" not in t2, "断言失败：循环解释仍在"
        assert "must enter through the restoring coefficient" in t2, "断言失败：新表述未写入"
        print("  ✅ 已改并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
