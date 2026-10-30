# -*- coding: utf-8 -*-
r"""应用 8/8 排序 + "sharp phase transition" 降级（2026-10-12）。

## 依据

- **排序证据比论文写的更强**：论文说 **6/6**（二项 p=0.031），
  成员穷举后是 **8/8**（精确二项 **p=0.0078**）→ `docs/P3_STATS.md §1.3`
- **"sharp phase transition" 降级**：r=5 的 bootstrap 95% CI **[−51.5, +12.5]** 跨零；
  r=5 vs r=6 精确置换（全枚举 20 种划分）**p=0.100**；n=3 vs n=3 的最小可检测效应
  **d=2.95** 而实测 **d=1.95** → **功效不足，单步不显著**
- **r=5 只声明"夹住交叉点"**（其符号随数值环境变化，见 `_p432`）

    python tools\_p433_apply_8of8_and_downgrade.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

PAIRS = [
    # ① 6/6 → 8/8，p 0.031 → 0.0078，并声明不是尖锐相变
    (
        "\\textbf{Result.} The crossing of $\\Delta E$ falls within $[4,6]$ for all\n"
        "four sample sizes and within $[5,6]$ for three of them, and the ordering\n"
        "$\\Delta E(r{=}6) > \\Delta E(r{=}5)$ is preserved in every configuration\n"
        "(6/6 configurations in total, including the phase table and\n"
        "ShareGPT; two-sided binomial $p = 0.031$, see the statistical test in\n"
        "Section~IV-B). The 16-sample configuration produces the same qualitative\n"
        "pattern as the 256-sample configuration, validating the experimental\n"
        "design.",
        "\\textbf{Result.} The crossing of $\\Delta E$ falls within $[4,6]$ for all\n"
        "four sample sizes and within $[5,6]$ for three of them, and the ordering\n"
        "$\\Delta E(r{=}6) > \\Delta E(r{=}5)$ is preserved in every configuration we\n"
        "ran (8/8, including the phase table and ShareGPT; two-sided binomial\n"
        "$p = 0.0078$, and the test in Section~IV-B). The 16-sample configuration\n"
        "produces the same qualitative pattern as the 256-sample configuration,\n"
        "validating the experimental design. We describe the transition as one whose\n"
        "\\emph{location is bracketed} by two ranks rather than as a sharp one: at\n"
        "$r=5$ the bootstrap $95\\%$ confidence interval $[-51.5, +12.5]$ spans zero, an\n"
        "exact permutation test between $r=5$ and $r=6$ gives $p = 0.100$, and with\n"
        "three seeds per rank the smallest detectable effect is $d = 2.95$ against an\n"
        "observed $d = 1.95$---the single-step contrast is underpowered, and it is the\n"
        "ordering across ranks, not the sharpness of any one step, that the data\n"
        "support.",
    ),
    # ② 把 3.1× 那句改为附带 worst-case（避免与 30× 段重复但保留数字）
    (
        "by $3.1\\times$, and $r=32$ Violation is uniformly c",
        "by $3.1\\times$, and $r=32$ Violation is uniformly c",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    total = 0
    for old, new in PAIRS:
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} 命中 {n}：{old[:60]!r}")
        if n == 1 and old != new:
            t = t.replace(old, new)
            total += 1
    if not a.apply:
        print("  （预演）")
        return 0
    if total:
        bak = EX.with_suffix(".tex.bak_p433")
        if not bak.exists():
            shutil.copy2(EX, bak)
        io.open(EX, "w", encoding="utf-8", newline="").write(t)
    print(f"\n  → 共改 {total} 处")
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "已改为 8/8": "(8/8, including the phase table" in t2,
        "已改为 p=0.0078": "$p = 0.0078$" in t2,
        "不再说 6/6 configurations": "(6/6 configurations in total" not in t2,
        "不再说 p=0.031": "$p = 0.031$" not in t2,
        "含 location is bracketed": "\\emph{location is bracketed}" in t2,
        "含 r=5 CI 跨零": "$[-51.5, +12.5]$" in t2,
        "含置换 p=0.100": "$p = 0.100$" in t2,
        "含功效不足（d=2.95 vs 1.95）": "$d = 2.95$" in t2 and "$d = 1.95$" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
