# -*- coding: utf-8 -*-
r"""用 500 对的重测结果更新 caption 与 limitation（2026-10-12）。

## 为什么

我先前用 `--pairs 300` 得出 **CG sd 0.00048 / R@1 sd 0.00714**。
审计成员指出：**噪声按 √(500/N) 放大**，且 **300 对的画廊更容易**（R@1 均值 0.682 vs 500 对的 0.579）。
**500 对重测后收敛为**：

| 量 | 500 对（采用） | 300 对（先前，弃用） | 归档对照 |
|---|---|---|---|
| **CG** | **0.818674 ± 0.000249** | 0.821335 ± 0.000475 | **0.8185**（差 0.0002） |
| **DG** | 0.865573 ± 0.000306 | 0.869171 ± 0.000409 | 0.8651（差 0.0005） |
| **R@1** | **0.578667 ± 0.005497** | 0.681667 ± 0.007136 | 审计测 **0.5770** |

→ **CG 抽样噪声 = 臂间差异（0.02–0.05）的 1/80–1/200**
→ **R@1 抽样噪声 0.0055 ≈ 臂间差异（0.01–0.07）的 1/2–1/13**

    python tools\_p389_update_noise_numbers.py [--apply]
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
     r"one checkpoint gives $R@1$ a standard deviation of $0.007$ over $300$ pairs while "
     r"$\mathrm{CG}$ varies by only $0.0005$",
     r"one checkpoint gives $R@1$ a standard deviation of $0.0055$ over $500$ pairs while "
     r"$\mathrm{CG}$ varies by only $0.00025$"),
    (E,
     r"whose sampling noise is two orders of magnitude below the between-arm differences",
     r"whose sampling noise is $80$--$200$ times below the between-arm differences"),
    (E,
     r"the remaining $R@1$ entries differ from the five-seed means by at most $0.0064$",
     r"the remaining $R@1$ entries differ from the five-seed means by at most $0.0064$, which "
     r"is of the same order as that sampling noise"),
    (D,
     r"Centroid Gap has a standard deviation of $0.0005$ and $R@1$ a standard deviation of "
     r"$0.007$",
     r"Centroid Gap has a standard deviation of $0.00025$ and $R@1$ a standard deviation of "
     r"$0.0055$"),
    (D,
     r"the between-arm differences they use are $40$--$100$ times that noise, but $R@1$ "
     r"differences below about $0.007$ should not be interpreted",
     r"the between-arm differences they use are $80$--$200$ times that noise, but $R@1$ "
     r"differences below about $0.006$ should not be interpreted"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new in PAIRS:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {n} ｜ {old[:56]}…")
        if n == 0:
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p369")
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
        "caption 用 0.00025 / 0.0055": "$0.00025$" in e and "$0.0055$" in e,
        "caption 用 80--200": "$80$--$200$" in e,
        "limitation 用 0.0055": "$0.0055$" in d,
        "limitation 用 0.006 阈值": "below about $0.006$" in d,
        # 判据必须绑定「抽样噪声」这个量，而不是字符串 "$0.007$"
        # （稿中 0.007 另有正当用法：±0.007 的 sd、p = 0.007）
        "caption 不再把抽样 sd 写成 0.007": "standard deviation of $0.007$" not in e,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
