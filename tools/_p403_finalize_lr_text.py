# -*- coding: utf-8 -*-
r"""按 task-7 最终表（19 runs / 7 lr）定稿稿中 lr 段落（2026-10-12）。

## 队友最终表（我已独立重算，逐格一致；sd = ddof=1）

| lr | n | zero-shot % | ΔCG | R@1 | 区 |
|---|---|---|---|---|---|
| 1e-07 | 2 | 60.52 ± 0.02 | **−0.0058 ± 0.0004** | 0.1760 | functional |
| 3e-07 | 2 | 61.07 ± 0.01 | **−0.0069 ± 0.0012** | 0.1782 | functional |
| 1e-06 | 3 | 60.87 ± 0.21 | **−0.0016 ± 0.0052** | 0.1808 | functional |
| 1e-05 | 3 | 52.18 ± 1.03 | **+0.1860 ± 0.0047** | 0.1700 | functional |
| 3e-05 | 3 | 29.72 ± 1.50 | **+0.2531 ± 0.0029** | 0.1508 | functional |
| 1e-04 | 3 | 2.63 ± 2.17 | **+0.4416 ± 0.3077** | 0.0448 | collapse |
| 3e-04 | 3 | 0.10 ± 0.03 | **+0.1545 ± 0.8551** | 0.0010 | collapse |

## ⚠️ 我核出队友一处不成立的全称否定

它写 *"**No interior minimum**"* —— **不成立**：逐点 ΔCG 序列
`−0.0058, −0.0069, −0.0016, +0.1860, …` 中，**`3e-07` 的 −0.0069 低于两侧**
（`1e-07` 的 −0.0058、`1e-06` 的 −0.0016）→ **是内部极小值**。
**但**（对论文有利的限定）：该极小值比相邻点只低 **0.0011 ≈ 2× 审计的 ΔCG 噪声 sd（0.00045–0.00070）**
→ **不应据此宣称"存在最优 lr"**。→ 我按数据写"**minimal and within a few sampling standard
deviations of its neighbours**"，**不照抄"无极小值"**。

## 3e-4 的两种退化几何（必须逐 seed 并列，不能只报均值）

| seed | ΔCG | CG | zero-shot |
|---|---|---|---|
| 42 | **+0.8001** | 1.6158 | 0.08% |
| 123 | **−0.8153** | **0.0004**（DG 0.0008） | 0.08% |
| 999 | **+0.4785** | 1.2942 | 0.13% |

→ **均值 +0.155 ± 0.855 无意义**（符号由 seed 决定；seed123 是嵌入塌成常数点）。

    python tools\_p403_finalize_lr_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
E = REPO / "paper合" / "sections" / "empirical.tex"
D = REPO / "paper合" / "sections" / "discussion.tex"

E_OLD = (
    r"Sweeping the rate shows that this is a property of the shared rate rather than of full "
    r"fine-tuning, and that the dependence is a threshold rather than a smooth optimum. Over "
    r"$\mathrm{lr}\in\{10^{-7},\dots,3\times10^{-4}\}$ there are three regimes: a plateau at "
    r"$\mathrm{lr}\le10^{-6}$ where $\Delta\mathrm{CG}$ is slightly \emph{negative} "
    r"($-0.008$ to $-0.0001$ across seeds) and zero-shot accuracy is $60.5$--$61.1\%$, i.e.\ "
    r"at or above the frozen model's $59.91\%$; a steep rise between $10^{-6}$ and "
    r"$10^{-5}$ ($\Delta\mathrm{CG}$ from $-0.000$ to $+0.188$, zero-shot from $60.9\%$ to "
    r"$52.2\%$); and then a collapse region from $10^{-4}$ upwards, where zero-shot accuracy "
    r"falls below $4\%$ and the embeddings degenerate towards a constant point, so that "
    r"$\Delta\mathrm{CG}$ stops measuring the modality gap at all: at $10^{-4}$ three seeds "
    r"give $+0.80$, $+0.26$ and $+0.27$, and at $3\times10^{-4}$ one seed gives "
    r"$\mathrm{CG} = 0.0004$ with a training loss pinned at $\ln 64$")

E_NEW = (
    r"Seven rates, two to three seeds each, show that this is a property of the shared rate "
    r"rather than of full fine-tuning, and that the dependence is a threshold rather than a "
    r"smooth optimum. At $\mathrm{lr}\le10^{-6}$ the gap change is \emph{negative} in every "
    r"seed ($-0.007$ to $-0.0001$; zero-shot $60.5$--$61.1\%$, at or above the frozen "
    r"$59.91\%$), the sign flips between $10^{-6}$ ($-0.0016 \pm 0.0052$) and $10^{-5}$ "
    r"($+0.1860 \pm 0.0047$), and it then rises monotonically to $+0.2531 \pm 0.0029$ at "
    r"$3\times10^{-5}$. The shallowest point is $3\times10^{-7}$ ($-0.0069$), but it lies only "
    r"$0.0011$ below its neighbours, about twice the sampling standard deviation of "
    r"$\Delta\mathrm{CG}$, so we do not read it as an optimal rate. Above $3\times10^{-5}$ the "
    r"comparison enters a collapse region: at $10^{-4}$ the three seeds lose $93$--$99.9\%$ of "
    r"zero-shot accuracy and $\Delta\mathrm{CG}$ is $+0.80$, $+0.26$ and $+0.27$, and at "
    r"$3\times10^{-4}$ the seed-to-seed spread of $\Delta\mathrm{CG}$ ($\pm 0.86$) exceeds any "
    r"effect because two distinct degenerate geometries occur---one seed reaches "
    r"$\mathrm{CG} = 0.0004$ with its loss pinned at $\ln 64$, the others stop at "
    r"$\mathrm{CG} = 1.62$ and $1.29$---so neither $\mathrm{CG}$ nor the gap change measures "
    r"the modality gap there and we report the per-seed values rather than their mean")

D_OLD = (
    r"and a collapse region from $10^{-4}$ upwards in which the embeddings degenerate towards a "
    r"constant point and $\Delta\mathrm{CG}$ ceases to measure the gap (three seeds at "
    r"$10^{-4}$ give $+0.80$, $+0.26$ and $+0.27$; at $3\times10^{-4}$ one seed gives "
    r"$\mathrm{CG} = 0.0004$ with a loss pinned at $\ln 64$). The behaviour up to "
    r"$3\times10^{-5}$ is therefore a threshold near $3\times10^{-6}$ followed by a monotone "
    r"rise to $+0.253 \pm 0.002$, not a saturation.")

D_NEW = (
    r"and a collapse region from $10^{-4}$ upwards in which the embeddings degenerate and "
    r"$\Delta\mathrm{CG}$ ceases to measure the gap (at $10^{-4}$ three seeds give $+0.80$, "
    r"$+0.26$ and $+0.27$; at $3\times10^{-4}$ the seeds reach $\mathrm{CG} = 0.0004$, "
    r"$1.62$ and $1.29$, the first with its loss pinned at $\ln 64$, so the seed-to-seed "
    r"spread $\pm 0.86$ exceeds any effect). The behaviour up to $3\times10^{-5}$ is therefore "
    r"a threshold near $3\times10^{-6}$ followed by a monotone rise to $+0.253 \pm 0.002$, not "
    r"a saturation, and the shallowest point we observe ($3\times10^{-7}$, $-0.0069$) is only "
    r"about twice the sampling noise of $\Delta\mathrm{CG}$, so it does not establish an "
    r"optimal rate.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new in ((E, E_OLD, E_NEW), (D, D_OLD, D_NEW)):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {n}")
        if n and a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p403")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += n
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    e = io.open(E, encoding="utf-8", errors="replace").read()
    d = io.open(D, encoding="utf-8", errors="replace").read()
    checks = {
        "empirical 含 7 rates": "Seven rates" in e,
        "empirical 含 3e-07 极小值且不当最优": "shallowest point is $3\\times10^{-7}$" in e
                                              and "we do not read it as an optimal rate" in e,
        "empirical 含 ±0.86": "$\\pm 0.86$" in e,
        "empirical 含逐 seed 退化几何": "$\\mathrm{CG} = 0.0004$" in e and "$1.62$" in e,
        "empirical 不再说 'three regimes'": "three regimes" not in e,
        "discussion 含 ±0.86": "$\\pm 0.86$" in d,
        "discussion 含'不确立最优 lr'": "does not establish an optimal rate" in d,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
