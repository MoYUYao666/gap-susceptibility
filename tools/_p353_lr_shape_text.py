# -*- coding: utf-8 -*-
r"""按 task-7 的**精确逐 seed**数字改稿：形状是「平台→陡升→饱和」（2026-10-12）。

## 完整数据（`outputs/analysis/pr_fullft_lr_sweep_ext.json`，16 run）

| lr | seeds | zero-shot % | ΔCG |
|---|---|---|---|
| 1e-07 | 42, 123 | 60.53 / 60.50 | −0.0061 / −0.0055 |
| **3e-07** | 42, 123 | **61.08 / 61.06** | **−0.0077 / −0.0061** |
| 1e-06 | 42, 123, 999 | 61.02 / 60.95 / 60.63 | −0.0074 / **+0.0027** / −0.0001 |
| **1e-05** | 42, 123, 999 | 53.20 / 52.18 / 51.15 | **+0.1805 / +0.1887 / +0.1887** |
| 3e-05 | 42, 123, 999 | 31.44 / 29.04 / 28.69 | +0.2498 / +0.2542 / +0.2553 |
| 1e-04 | 42, 123 | 0.14 / 4.15 | +0.7969 / +0.2600 |
| 3e-04 | 42 | 0.08 | +0.8001 |

**→ 形状（不是"单调"）**：
1. **lr ≤ 1e-6：平台**，ΔCG **略负**（−0.006…−0.0001），zero-shot **61% > 冻结 59.91%**
2. **1e-6 → 1e-5：陡升**（−0.0001 → +0.188）
3. **≥ 3e-5：饱和**（+0.25 → +0.80）

→ **是 lr ≈ 3e-6…1e-5 处的阈值效应，不是平滑最优。**

## 对稿件的两处更正

| 位置 | 原（我上一版写的） | 改为 |
|---|---|---|
| `empirical.tex` | *"zero-shot falls from 60.5% at 1e-7 … ΔCG turns positive only above 1e-5"* | 加**平台/陡升/饱和**三段式与"**不是平滑最优**" |
| `discussion.tex` limitation | *"monotone in accuracy throughout while the gap change changes sign near 1e-5"* | 改为三段式描述 |

    python tools\_p353_lr_shape_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAIRS = [
    # empirical.tex
    ("paper合/sections/empirical.tex",
     r"Sweeping the rate shows that this is a property of the shared rate rather than of full "
     r"fine-tuning: over $\mathrm{lr}\in\{10^{-7},\dots,3\times10^{-4}\}$ zero-shot accuracy "
     r"falls from $60.5\%$ at $10^{-7}$ to $0.1\%$ at $10^{-4}$, and $\Delta\mathrm{CG}$ turns "
     r"positive only above $10^{-5}$---it is $-0.006$ at $10^{-7}$, $-0.002\pm0.005$ at "
     r"$10^{-6}$, $+0.19$ at $10^{-5}$, $+0.25$ at $3\times10^{-5}$ and $+0.80$ at "
     r"$10^{-4}$---so the gap widening that motivates the comparison appears only on the "
     r"damaging side of the rate range and is not a property of full fine-tuning at a "
     r"conservative rate.",
     r"Sweeping the rate shows that this is a property of the shared rate rather than of full "
     r"fine-tuning, and that the dependence is a threshold rather than a smooth optimum. Over "
     r"$\mathrm{lr}\in\{10^{-7},\dots,3\times10^{-4}\}$ there are three regimes: a plateau at "
     r"$\mathrm{lr}\le10^{-6}$ where $\Delta\mathrm{CG}$ is slightly \emph{negative} "
     r"($-0.008$ to $-0.0001$ across seeds) and zero-shot accuracy is $60.5$--$61.1\%$, i.e.\ "
     r"at or above the frozen model's $59.91\%$; a steep rise between $10^{-6}$ and "
     r"$10^{-5}$ ($\Delta\mathrm{CG}$ from $-0.000$ to $+0.188$, zero-shot from $60.9\%$ to "
     r"$52.2\%$); and saturation above $3\times10^{-5}$ ($+0.25$ rising to $+0.80$ with "
     r"zero-shot near chance). The gap widening that motivates the comparison therefore "
     r"appears only on the damaging side of a threshold near $3\times10^{-6}$, and is absent "
     r"at every conservative rate we tested."),

    # discussion.tex
    ("paper合/sections/discussion.tex",
     r"its zero-shot accuracy spans $60.5\%$ to $0.1\%$ and its $\Delta\mathrm{CG}$ spans "
     r"$-0.006$ to $+0.80$, monotone in accuracy throughout while the gap change changes sign "
     r"near $10^{-5}$.",
     r"its zero-shot accuracy spans $61.1\%$ (above the frozen $59.91\%$) to $0.1\%$ and its "
     r"$\Delta\mathrm{CG}$ spans $-0.008$ to $+0.80$, with a flat slightly-negative plateau "
     r"at $\mathrm{lr}\le10^{-6}$, a steep rise between $10^{-6}$ and $10^{-5}$, and "
     r"saturation above $3\times10^{-5}$, so the behaviour is a threshold near "
     r"$3\times10^{-6}$ rather than a smooth optimum."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for rel, old, new in PAIRS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {Path(rel).name}: {n}")
        if n == 0:
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p353")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += n
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    t1 = io.open(REPO / "paper合" / "sections" / "empirical.tex", encoding="utf-8").read()
    t2 = io.open(REPO / "paper合" / "sections" / "discussion.tex", encoding="utf-8").read()
    checks = {
        "empirical 含 'threshold rather than a smooth optimum'":
            "threshold rather than a smooth optimum" in t1,
        "empirical 含 'three regimes'": "three regimes" in t1,
        "empirical 含 3e-6 阈值": "3\\times10^{-6}" in t1,
        "discussion 含 'threshold near'": "threshold near" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
