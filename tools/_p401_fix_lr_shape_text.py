# -*- coding: utf-8 -*-
r"""按 task-7 完整数据修正稿中的 lr 形状表述（2026-10-12）。

## 我先前写错的

我写 *"…and saturation above $3\times10^{-5}$（+0.25 升到 +0.80…）"* ——
**"饱和/平台"不成立**：`1e-4` 三个 seed 是 **+0.7969 / +0.2600 / +0.2679**（sd **0.25**），
只有 seed42 在 ≈+0.80；`3e-4` 更进入**退化塌缩**（seed123：**CG 0.0004 / DG 0.0008** → 嵌入塌成常数点，
CG/DG 不再是间隙度量）。

## 已核实（`tools/_p400` → `outputs/analysis/lr_table_verified.json`）

| lr | n | ΔCG | zero-shot |
|---|---|---|---|
| 1e-07 | 2 | **−0.0058 ± 0.0003** | 60.52% |
| 3e-07 | 2 | **−0.0069 ± 0.0008** | 61.07% |
| 1e-06 | 3 | **−0.0016 ± 0.0043** | 60.87% |
| 1e-05 | 3 | **+0.1860 ± 0.0038** | 52.18% |
| 3e-05 | 3 | **+0.2531 ± 0.0024** | 29.72% |
| 1e-04 | 3 | **+0.4416 ± 0.2512**（0.797/0.260/0.268） | 2.63% |
| 3e-04 | 2 | **−0.0076 ± 0.8077**（0.800/**−0.815**） | 0.08% |

**成立的两条**：lr ≤ 1e-6 **平台且略负**；1e-6→1e-5 **陡升**。
**不成立的**：≥3e-5"饱和"——`1e-4` 起进入**塌缩区**。

## 顺带强化 C 项（队友的 seed 特异发现）

`1e-4` 的复现**按 seed 命中归档**：seed123 = 4.15% / +0.2600 vs 归档 **4.12% / +0.2609**；
seed999 = 3.59% / +0.2679 vs 归档 **3.39% / +0.2672**；**只有 seed42 分叉**
（+0.797 vs 归档 +0.665，但 zero-shot 0.14 vs 0.13% 一致）
⇒ **环境本身可复现，分叉只出现在完全塌缩的那个 seed**。

    python tools\_p401_fix_lr_shape_text.py [--apply]
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

PAIRS = [
    (E,
     r"and saturation above $3\times10^{-5}$ ($+0.25$ rising to $+0.80$ with zero-shot near "
     r"chance)",
     r"and then a collapse region from $10^{-4}$ upwards, where zero-shot accuracy falls below "
     r"$4\%$ and the embeddings degenerate towards a constant point, so that $\Delta\mathrm{CG}$ "
     r"stops measuring the modality gap at all: at $10^{-4}$ three seeds give "
     r"$+0.80$, $+0.26$ and $+0.27$, and at $3\times10^{-4}$ one seed gives "
     r"$\mathrm{CG} = 0.0004$ with a training loss pinned at $\ln 64$"),
    (D,
     r"saturation above $3\times10^{-5}$, so the behaviour is a threshold near "
     r"$3\times10^{-6}$ rather than a smooth optimum.",
     r"and a collapse region from $10^{-4}$ upwards in which the embeddings degenerate towards a "
     r"constant point and $\Delta\mathrm{CG}$ ceases to measure the gap (three seeds at "
     r"$10^{-4}$ give $+0.80$, $+0.26$ and $+0.27$; at $3\times10^{-4}$ one seed gives "
     r"$\mathrm{CG} = 0.0004$ with a loss pinned at $\ln 64$). The behaviour up to "
     r"$3\times10^{-5}$ is therefore a threshold near $3\times10^{-6}$ followed by a monotone "
     r"rise to $+0.253 \pm 0.002$, not a saturation."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new in PAIRS:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {n}")
        if n and a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p401")
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
        "empirical 含 collapse region": "collapse region from $10^{-4}$" in e,
        "empirical 含 ln 64": "$\\ln 64$" in e,
        "empirical 不再说 'saturation above'": "saturation above $3\\times10^{-5}$" not in e,
        "discussion 含 collapse region": "collapse region from $10^{-4}$" in d,
        "discussion 含 0.253 与'not a saturation'": "$+0.253 \\pm 0.002$" in d and "not a saturation" in d,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
