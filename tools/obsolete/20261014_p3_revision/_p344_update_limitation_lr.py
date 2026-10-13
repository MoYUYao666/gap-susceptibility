# -*- coding: utf-8 -*-
r"""同步更新 `discussion.tex` 里 Tenth limitation 的 lr 范围（2026-10-12）。

**task-7** 把网格从 `{1e-6…3e-4}` 扩到 **`{1e-7…3e-4}`**：
- 1e-7：zero-shot **60.53%**、**ΔCG −0.0061**
- 1e-6：60.87 ± 0.21%、ΔCG −0.0016
→ 原文 *"spans 60.9% to 0.1% and its ΔCG spans −0.002 to +0.80"* 需改为
**60.5%–0.1%** 与 **−0.006–+0.80**，并说明**符号翻转点在 1e-5 附近**。

    python tools\_p344_update_limitation_lr.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

OLD = (r"than the adapter methods: over $\mathrm{lr}\in\{10^{-6},\dots,3\times10^{-4}\}$ its "
       r"zero-shot accuracy spans $60.9\%$ to $0.1\%$ and its $\Delta\mathrm{CG}$ spans "
       r"$-0.002$ to $+0.80$, monotonically.")

NEW = (r"than the adapter methods: over $\mathrm{lr}\in\{10^{-7},\dots,3\times10^{-4}\}$ its "
       r"zero-shot accuracy spans $60.5\%$ to $0.1\%$ and its $\Delta\mathrm{CG}$ spans "
       r"$-0.006$ to $+0.80$, monotone in accuracy throughout while the gap change changes "
       r"sign near $10^{-5}$.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n == 0:
        i = t.find("zero-shot accuracy spans")
        print("  附近: " + repr(t[max(0, i - 220):i + 260]) if i >= 0 else "  （找不到）")
        return 1
    t2 = t.replace(OLD, NEW)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p344")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "含 1e-7 范围": "$10^{-7}$" in t3 and "$60.5\\%$" in t3,
        "含符号翻转说明": "changes sign near $10^{-5}$" in t3,
        "旧 60.9% 已去": "$60.9\\%$ to $0.1\\%$" not in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
