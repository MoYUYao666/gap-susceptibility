# -*- coding: utf-8 -*-
r"""决定用哪个分配变体：对两个候选做**同一组性质检查**，一次看清。

性质：
 P1 β=0 是否给出 rank-uniform（论文原话 "β→0 degenerates to uniform"）
 P2 β=0 是否给出**参数均匀**（R3.21 要的"等价有效参数预算"）
 P3 β→∞ 是否达到线性目标 `Σ|Γ|·rank` 最优
 P4 单调性（β↗ ⇒ 高|Γ|块 rank 不增）
"""
from __future__ import annotations
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_alloc_solvers import (BLOCKS, solve_corner_exact, solve_softmin_weights,
                                 uniform_plan)

COST = {"vision": 655360, "llm_shallow": 247296, "llm_mid": 577024, "llm_deep": 329728}
B = 4 * sum(COST.values())          # 主实验预算（uniform r=4）
G = {"vision": 3.7e8, "llm_shallow": 9.0e2, "llm_mid": 2.1e3, "llm_deep": 7.2e3}
G2 = {"vision": 8092.0, "llm_shallow": 1614.0, "llm_mid": 8717.0, "llm_deep": 2727.0}

print(f"B = {B:,}｜uniform 整数解 = {uniform_plan(COST, B)['ranks']}")
print(f"uniform 解的逐块参数 = "
      f"{ {b: uniform_plan(COST, B)['ranks'][b]*COST[b] for b in BLOCKS} }\n")

for case, g in (("cross_magnitude", G), ("llava_like", G2)):
    print(f"########## {case} ##########")
    for ca in (False, True):
        tag = "cost_aware" if ca else "literal"
        r0 = solve_softmin_weights(g, COST, B, 0.0, cost_aware=ca)["ranks"]
        p0 = {b: r0[b] * COST[b] for b in BLOCKS}
        p1_beta0 = "YES" if len(set(p0.values())) == 1 else "no"
        p1_rankuni = "YES" if len(set(r0.values())) == 1 else "no"
        rinf = solve_softmin_weights(g, COST, B, 1e9, cost_aware=ca)["ranks"]
        opt = solve_corner_exact(g, COST, B)["ranks"]
        o_inf = sum(g[b] * rinf[b] for b in BLOCKS)
        o_opt = sum(g[b] * opt[b] for b in BLOCKS)
        p3 = "YES" if abs(o_inf - o_opt) <= 1e-6 * max(abs(o_opt), 1.0) else "no"
        # 单调性
        prev, mono = None, "YES"
        for beta in (0.0, 1e-4, 1e-3, 0.137, 1.0, 1e3, 1e9):
            r = solve_softmin_weights(g, COST, B, beta, cost_aware=ca)["ranks"]
            hi = max(BLOCKS, key=lambda b: abs(g[b]))
            if prev is not None and r[hi] > prev[hi]:
                mono = f"no (β={beta}: {prev[hi]}→{r[hi]})"
                break
            prev = r
        print(f"  [{tag:<10}] P1 rank-uniform@β=0: {p1_rankuni:<4}"
              f" P2 param-uniform@β=0: {p1_beta0:<4}"
              f" P3 β→∞最优: {p3:<4} P4 单调: {mono}")
        print(f"             β=0  → {r0}  参数 { {b: p0[b] for b in BLOCKS} }")
        print(f"             β=1e9→ {rinf}  obj={o_inf:.6g} (opt {o_opt:.6g})")
    print()
