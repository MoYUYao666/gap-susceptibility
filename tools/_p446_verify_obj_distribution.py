# -*- coding: utf-8 -*-
r"""核独立随机样本的 obj 分布（2026-10-13）。

## 待核

10 个独立随机样本（`random_01,02,03,05..11`）的 `linear_objective` 分布；
`random_05` 是否真的 **obj 26,527** 且几乎等于 Γ-guided 的 **25,356**（**关键对照点**）。

    python tools\_p446_verify_obj_distribution.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_random_obj_distribution.json"

INDEPENDENT = ["random_01", "random_02", "random_03", "random_05", "random_06",
               "random_07", "random_08", "random_09", "random_10", "random_11"]
KNOWN_DUP = {"random_00": "exp_ca_beta_1e-4", "random_04": "corner",
             "random_12": "inverse_beta_paper_0.137",
             "random_13": "exp_beta_paper_0.137"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(REPO / "outputs/analysis/p3_alloc_plans.json",
                           encoding="utf-8", errors="replace").read())
    p = d["plans"]

    print("=" * 100)
    print("① 10 个独立随机样本的 obj")
    print("=" * 100)
    rows = []
    for n in INDEPENDENT:
        if n not in p:
            print(f"  ⚠️ 缺 {n}")
            continue
        obj = p[n].get("linear_objective")
        rows.append((n, obj))
    for n, obj in sorted(rows, key=lambda x: x[1]):
        print(f"  {n:<12} obj = {obj:>10,.0f}")
    if rows:
        vals = [x[1] for x in rows]
        print(f"\n  n={len(vals)} ｜ min {min(vals):,.0f} ｜ max {max(vals):,.0f} "
              f"｜ 中位数 {statistics.median(vals):,.0f} ｜ 均值 {statistics.mean(vals):,.0f}")

    print()
    print("=" * 100)
    print("② 关键对照：Γ-guided 与规则解的 obj")
    print("=" * 100)
    refs = {"exp（Γ-guided，论文 β=0.137）": "exp_beta_paper_0.137",
            "uniform": "uniform",
            "random_00（= exp_ca 1e-4，**不是随机**）": "random_00",
            "exp_ca_beta_1e-4（= random_00）": "exp_ca_beta_1e-4",
            "inverse（反序）": "inverse_beta_paper_0.137",
            "corner": "corner"}
    for label, n in refs.items():
        if n in p:
            print(f"  {label:<44} obj = {p[n].get('linear_objective'):>10,.0f}")

    print()
    print("=" * 100)
    print("③ 哪些独立随机样本的 obj 低于 Γ-guided（25,356）？")
    print("=" * 100)
    g = p["exp_beta_paper_0.137"]["linear_objective"]
    lower = [(n, o) for n, o in rows if o < g]
    print(f"  Γ-guided obj = {g:,.0f}")
    if lower:
        for n, o in sorted(lower, key=lambda x: x[1]):
            print(f"  ⚠️ {n:<12} obj {o:>10,.0f}（低 {100*(g-o)/g:.1f}%）→ 按线性目标应**不差于** Γ-guided")
    else:
        print("  ✅ 没有独立随机样本的 obj 低于 Γ-guided")

    res = {"independent_random_obj": {n: o for n, o in rows},
           "gamma_obj": g,
           "independent_lower_than_gamma": [n for n, _ in lower],
           "known_rule_duplicates": KNOWN_DUP}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
