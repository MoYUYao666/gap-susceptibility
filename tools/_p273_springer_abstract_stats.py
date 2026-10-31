# -*- coding: utf-8 -*-
r"""把统计限制段插入 Springer 摘要（`\abstract{...}`，以单独一行的 `}` 结束）（2026-10-12）。

    python tools\_p273_springer_abstract_stats.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "main_springer.tex"

ANCHOR = ("is a property of the architecture, not a universal default.\n"
          "}\n")

ADD = (
    "is a property of the architecture, not a universal default.\n"
    "Because the runs are nested rather than independent, we report the gap--retrieval\n"
    "association with cluster-robust inference: under dataset $\\times$ backbone clustering the\n"
    "slope is $-1.05$ (CR1 standard error $0.29$, $p=0.016$), the family-clustered bootstrap\n"
    "95\\% interval is $[-0.89,-0.62]$, and a mixed model with random intercepts for dataset,\n"
    "backbone and configuration gives $\\beta=-0.95\\pm0.08$. The within-cell and between-cell\n"
    "slopes agree ($-1.07$ vs $-1.01$), so the relation is not a between-group artefact, but its\n"
    "precision is much lower than $n=204$ suggests.\n"
    "}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    if "cluster-robust inference" in t:
        print("  已存在，跳过")
        return 0
    n = t.count(ANCHOR)
    print(f"  锚点命中 {n}")
    if n != 1:
        i = t.find("not a universal default")
        print("  附近: " + repr(t[max(0, i - 80):i + 120]))
        return 1
    t2 = t.replace(ANCHOR, ADD, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = "cluster-robust inference" in t3 and "\\beta=-0.95\\pm0.08" in t3
    print(f"  {'✅ 已插入' if ok else '🔴 失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
