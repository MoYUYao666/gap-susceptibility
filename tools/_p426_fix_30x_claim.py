# -*- coding: utf-8 -*-
r"""图注与结果段的 "30×" 加消歧（2026-10-12）。

## 依据（`p3-stats` 发现，我已核实）

27 vs 808 的比较里 **$\eta^2(\mathrm{rank}) = 0.989$** —— 808 的 sd **几乎全部来自"抽到哪个 rank"**；
**同秩 r=4 对 r=4 的 sd 比 = 0.98（不是 30×）**、Welch **p=0.47**。

## 与 `_p425` 的关系

`_p425` 修的是**设计描述**（三组容量不等，16×）；本脚本修的是**结论主张**
（"30× demonstrating …"）→ 两者是同一处缺陷的**两个面**，需一起改。

    python tools\_p426_fix_30x_claim.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

# 图注
CAP_OLD = (
    "Theory (r=4) achieves low alignment\n"
    "degradation with small variance. Random allocation suffers $30\\times$ larger\n"
    "standard deviation ($808$ vs.\\ $27$).")
CAP_NEW = (
    "Theory (r=4) achieves low alignment\n"
    "degradation with small variance; the Random group's larger spread across its\n"
    "15 runs ($808$ vs.\\ $27$ in sample std) is confounded with capacity, since that\n"
    "group draws its rank from a $16$-fold range (Section~IV-E).")

# 结果段
RES_OLD = (
    "Random allocation produces $\\Delta E = 491 \\pm 808$ (sample std over 15 runs)---the\n"
    "standard deviation is $30\\times$ larger ($808$ vs.\\ $27$), demonstrating")
RES_NEW = (
    "Random allocation produces $\\Delta E = 491 \\pm 808$ (sample std over 15 runs).\n"
    "That spread is $30\\times$ the Theory group's ($808$ vs.\\ $27$), but it is not a\n"
    "clean measure of allocation uncertainty: the Random group's rank is drawn from\n"
    "$\\{4,16,32,64\\}$, so rank---and hence capacity---explains almost all of it. We\n"
    "therefore do not read the ratio as evidence of allocation, demonstrating only")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    total = 0
    for old, new, label in ((CAP_OLD, CAP_NEW, "图注 30×"),
                            (RES_OLD, RES_NEW, "结果段 30×")):
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {label} 命中 {n}")
        if n == 1:
            t = t.replace(old, new)
            total += 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p426")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)
    print(f"\n  → 共改 {total} 处")
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "图注不再无保留地说 30×": "suffers $30\\times$ larger" not in t2,
        "图注点明与容量混淆": "is confounded with capacity" in t2,
        "结果段说 rank 解释几乎全部": "explains almost all of it" in t2,
        "结果段声明不把比值当分配证据": "do not read the ratio as evidence of allocation" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
