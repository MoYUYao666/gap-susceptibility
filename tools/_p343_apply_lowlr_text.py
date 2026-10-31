# -*- coding: utf-8 -*-
r"""把 task-7 的低 lr 结果写进 `empirical.tex` 的全量微调段（2026-10-12）。

## 现有（已过时）

> over $\mathrm{lr}\in\{10^{-6},\dots,3\times10^{-4}\}$ the damage is **monotone**,
> with zero-shot accuracy falling from $60.9\pm0.2\%$ at $10^{-6}$ to $0.1\%$ at $10^{-4}$,
> and $\Delta\mathrm{CG}$ going from $-0.002\pm0.005$ to $+0.80$.

## 新数据（`outputs/analysis/pr_fullft_lr_sweep_ext.json`）

| lr | zero-shot | ΔCG |
|---|---|---|
| **1e-7** | **60.53%** | **−0.0061** |
| 1e-6 | 60.87 ± 0.21% | −0.0016 |
| 1e-5 | 52.18 ± 1.03% | +0.186 |
| 3e-5 | 31.44% | +0.2498 |
| 1e-4 | 0.14% | +0.7969 |
| 3e-4 | 0.08% | +0.8001 |

**→ "单调"不准确**：损伤在 lr 上确实单调增大，但 **ΔCG 的符号在 lr ≤ 1e-6 为负**，
**间隙扩大只在 lr ≥ 1e-5 出现**（存在极小值）。

    python tools\_p343_apply_lowlr_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = (
    r"Sweeping the rate shows that this is a property of the shared rate rather than of full "
    r"fine-tuning: over $\mathrm{lr}\in\{10^{-6},\dots,3\times10^{-4}\}$ the damage is "
    r"monotone, with zero-shot accuracy falling from $60.9\pm0.2\%$ at $10^{-6}$ to $0.1\%$ at "
    r"$10^{-4}$, and $\Delta\mathrm{CG}$ going from $-0.002\pm0.005$ to $+0.80$. At "
    r"$10^{-6}$ full fine-tuning is therefore indistinguishable from the frozen model in "
    r"alignment, slightly better in zero-shot accuracy, and better in-domain "
    r"($R@1 = 0.181$ against $0.156$ frozen),")

NEW = (
    r"Sweeping the rate shows that this is a property of the shared rate rather than of full "
    r"fine-tuning: over $\mathrm{lr}\in\{10^{-7},\dots,3\times10^{-4}\}$ zero-shot accuracy "
    r"falls from $60.5\%$ at $10^{-7}$ to $0.1\%$ at $10^{-4}$, and $\Delta\mathrm{CG}$ turns "
    r"positive only above $10^{-5}$---it is $-0.006$ at $10^{-7}$, $-0.002\pm0.005$ at "
    r"$10^{-6}$, $+0.19$ at $10^{-5}$, $+0.25$ at $3\times10^{-5}$ and $+0.80$ at "
    r"$10^{-4}$---so the gap widening that motivates the comparison appears only on the "
    r"damaging side of the rate range and is not a property of full fine-tuning at a "
    r"conservative rate. At $10^{-6}$ full fine-tuning is therefore indistinguishable from "
    r"the frozen model in alignment, slightly better in zero-shot accuracy, and better "
    r"in-domain ($R@1 = 0.181$ against $0.156$ frozen),")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        print("  🔴 未命中")
        return 1
    t2 = t.replace(OLD, NEW)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p343")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "含 1e-7 的 60.5%": "$60.5\\%$ at $10^{-7}$" in t3,
        "含 1e-7 的 ΔCG −0.006": "$-0.006$ at $10^{-7}$" in t3,
        "含 'turns positive only above'": "turns positive only above $10^{-5}$" in t3,
        "旧的 'monotone' 说法已去": "the damage is \\nmonotone" not in t3 and "damage is monotone" not in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
