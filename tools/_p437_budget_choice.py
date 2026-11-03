# -*- coding: utf-8 -*-
r"""选择实验预算：统计每个候选预算下**精确命中**的分配方案有多少个。

为什么要这一步：论文 now 的 Theory 组是 uniform r=4（预算 7,237,632）。
但如果某个预算在整数格点上只允许 **1–3 种**分配，那"非均匀 vs 均匀"的对比就没有
自由度，实验本身没有信息量。本脚本扫 uniform r=1..12，给出：

- 精确可行解个数（自由度）；
- 逐块 rank 的取值范围；
- 张成该预算所需的 rank 总和。

    python tools\_p437_budget_choice.py
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_alloc_solvers import BLOCKS, is_feasible, rank_bounds  # noqa: E402

COST = {"vision": 655360, "llm_shallow": 247296, "llm_mid": 577024, "llm_deep": 329728}
SUM_COST = sum(COST.values())


def count_exact(budget, min_rank=1, cap=2_000_000):
    """精确命中预算的整数解个数（超过 cap 就截断，只报"≥cap"）。"""
    hi = rank_bounds(COST, budget, min_rank)
    if any(hi[b] < min_rank for b in BLOCKS):
        return None, hi
    n = 0
    last = min(BLOCKS, key=lambda b: COST[b])
    outer = [b for b in BLOCKS if b != last]
    a, b_, c = outer
    for va in range(min_rank, min(hi[a], 400) + 1):
        for vb in range(min_rank, min(hi[b_], 400) + 1):
            for vc in range(min_rank, min(hi[c], 400) + 1):
                num = budget - (va * COST[a] + vb * COST[b_] + vc * COST[c])
                if num < 0:
                    continue
                if num % COST[last]:
                    continue
                vd = num // COST[last]
                if vd < min_rank or vd > hi[last]:
                    continue
                n += 1
                if n >= cap:
                    return f">={cap}", hi
    return n, hi


def main() -> int:
    print(f"cost/rank: {COST}")
    print(f"Σcost = {SUM_COST:,}")
    print(f"最小可行预算（各块 rank=1）= {SUM_COST:,}\n")
    print(f"{'uniform r':>10}{'预算':>14}{'可行解个数':>14}{'rank 上界':>34}{'rank 总和范围':>18}")
    rows = []
    for r in range(1, 13):
        budget = r * SUM_COST
        n, hi = count_exact(budget)
        ok, _ = is_feasible(COST, budget)
        lo_sum = sum(1 for _ in BLOCKS)
        # 最小/最大可能 rank 总和（受预算约束）
        rng = f"{lo_sum} – {sum(hi.values())}"
        print(f"{r:>10}{budget:>14,}{str(n):>14}{str(hi):>34}{rng:>18}")
        rows.append({"uniform_r": r, "budget": budget, "n_exact_allocations": n,
                     "rank_upper_bounds": hi, "rank_sum_range": rng})

    print("\n=== 判读 ===")
    for row in rows:
        n = row["n_exact_allocations"]
        if isinstance(n, int) and n >= 20:
            print(f"  uniform r={row['uniform_r']}（B={row['budget']:,}）有 {n}+ 个精确解 → "
                  f"**有自由度，适合做非均匀对比**")
            break
    else:
        print("  没有预算给出 ≥20 个精确解——所有预算的整数格点都很稀疏")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
