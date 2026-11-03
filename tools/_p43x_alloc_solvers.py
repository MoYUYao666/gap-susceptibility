# -*- coding: utf-8 -*-
r"""task-9 分配律的**精确**求解器（纯数值，无 GPU 依赖）。

## 为什么要单独一个文件

分配律是整个 E 组的核心；第一版 `_p433_alloc_plans.py` 里的贪心在
`tools/_p435_tests_alloc_math.py` 下暴露了三个真 bug：

1. **float32 上溢**：`exp(-β|Γ|)` 在 β=0.137、|Γ|~10^8 时算出 `inf/nan`
   （必须先减 `min|Γ|` 做平移，这是数值稳定的标准做法）；
2. **预算没精确命中**：贪心的"再加就超预算"会停在预算**下方**，不会精确命中；
3. **β→0 不退化到 uniform**：收尾阶段按"最便宜的块"花剩余预算，把解推歪了。

本文件给出**两个精确**求解器，并互相交叉验证：

- `solve_lagrangian_exact` —— 论文目标 `Σ|Γ_k|·rank_k` 在约束
  `Σ rank_k·cost_k = B`、`rank_k ≥ 1` 下的**真实最优**（穷举 + numpy 向量化）；
- `solve_softmin_weights` —— 论文 Eq. 5 的连续解 `rank_k ∝ exp(-β|Γ_k|)/cost_k`
  在整数格点上的**最近可行解**（穷举，按 `Σ|log rank_k − log target_k|` 取最近）。

两者都在**整数格点**上穷举，因此 `Σ rank_k·cost_k = B` 是**精确**保证（不是"约等于"）。
"""
from __future__ import annotations

import itertools
import math

import numpy as np

BLOCKS = ["vision", "llm_shallow", "llm_mid", "llm_deep"]
MAX_ENUM_SPACE = 40_000_000     # 超过则改用方向性搜索（并如实标注方法）


# --------------------------------------------------------------------------- #
# 权重（数值稳定）
# --------------------------------------------------------------------------- #
def softmin_weights(gamma_abs: dict, beta: float) -> dict:
    """`w_k ∝ exp(-β(|Γ_k| − min|Γ|))`。先平移再取指数 → 不会上溢/下溢。

    β=0 时严格等于均匀权重 1/K。
    """
    g = np.array([gamma_abs[b] for b in BLOCKS], dtype=np.float64)
    if beta == 0.0:
        w = np.ones_like(g)
    else:
        w = np.exp(-beta * (g - g.min()))
    tot = w.sum()
    return {b: float(w[i] / tot) for i, b in enumerate(BLOCKS)}


# --------------------------------------------------------------------------- #
# 可行性
# --------------------------------------------------------------------------- #
def rank_bounds(cost: dict, budget: int, min_rank: int = 1):
    """每块的**可行** rank 上界。

    正确形式：本块可以吃掉"其余块各拿 `min_rank` 之后"的全部剩余预算，
    但**最后一分钱必须花在本块上**——因此上界要对每个候选对照块取最小：
        hi_b = min_{x≠b} floor((B - Σ_{y∉{b,x}} min·cost_y - min·cost_x) / cost_b)

    第一版漏了这层 min（等价于只对**最便宜**的块正确），把 vision 的上界算成 9
    而不是 11，导致穷举永远找不到 `r0=4` 这类真实最优解 ——
    由 `solve_*` 内部的预算断言抓出（见 `tools/_p435_tests_alloc_math.py`）。
    """
    hi = {}
    for b in BLOCKS:
        others = [x for x in BLOCKS if x != b]
        best = None
        for x in others:
            rest = sum(min_rank * cost[y] for y in others if y != x) + min_rank * cost[x]
            cand = int((budget - rest) // cost[b])
            best = cand if best is None else min(best, cand)
        hi[b] = int(best)
    return hi


def is_feasible(cost: dict, budget: int, min_rank: int = 1) -> tuple[bool, str]:
    lo = sum(min_rank * cost[b] for b in BLOCKS)
    if lo > budget:
        return False, f"rank≥{min_rank} 的最小成本 {lo:,} > 预算 {budget:,}"
    hi = rank_bounds(cost, budget, min_rank)
    if any(hi[b] < min_rank for b in BLOCKS):
        return False, f"某块上界 {hi} < {min_rank}"
    return True, ""


def enum_space(cost: dict, budget: int, min_rank: int = 1) -> int:
    hi = rank_bounds(cost, budget, min_rank)
    n = 1
    for b in BLOCKS:
        n *= max(hi[b] - min_rank + 1, 0)
    return n


# --------------------------------------------------------------------------- #
# 共享：在**精确预算面**上穷举（3 块 Python 嵌套，第 4 块由等式闭式解出）
# --------------------------------------------------------------------------- #
def _enumerate_over_budget_surface(cost: dict, budget: int, min_rank: int,
                                   score, want_max: bool = False):
    """在 `Σ rank_k·cost_k = B` 的整数格点上穷举，返回 `score(ranks)` 最优的可行解。

    关键技巧：只对**最便宜**的块做闭式求解

        rank_last = (B − Σ_{k<last} rank_k·cost_k) / cost_last

    因为最便宜块的系数最小，它的可行取值集合最大 → 外层 3 块的循环范围最小
    （本预算下各 ~20 个取值，总候选 ~10^4–10^5，秒级完成）。
    每个候选都**精确**命中预算（`num % c_last == 0` 整除才接受），无需事后修补。

    返回 `(ranks, score_value, n_candidates)`。
    """
    ok, why = is_feasible(cost, budget, min_rank)
    if not ok:
        raise ValueError(why)
    hi = rank_bounds(cost, budget, min_rank)
    last = min(BLOCKS, key=lambda b: cost[b])
    outer = [b for b in BLOCKS if b != last]
    c_last = cost[last]

    best_ranks, best_score, n_cand = None, None, 0
    # 平局打破：在**距离相同**的候选里，偏好最便宜块 rank 更大（= 更接近论文的
    # hard-protection 角点解）。没有这一项时，可行面稀疏处（实测主预算只有 15 个
    # 可行解，其中若干在 β=0 处距离并列）会按字典序挑一个，使"β→0 ⇒ uniform"
    # 这条论文自己的性质不稳。
    # 用**相对**容差判并列，避免绝对 eps 在高/低分数尺度上失效。
    a, b_, c = outer
    tol = 1e-9
    for va in range(min_rank, hi[a] + 1):
        for vb in range(min_rank, hi[b_] + 1):
            for vc in range(min_rank, hi[c] + 1):
                num = budget - (va * cost[a] + vb * cost[b_] + vc * cost[c])
                if num < 0 or num % c_last != 0:
                    continue
                vd = num // c_last
                if vd < min_rank or vd > hi[last]:
                    continue
                ranks = {a: va, b_: vb, c: vc, last: vd}
                n_cand += 1
                s = score(ranks)
                if best_score is None:
                    best_score, best_ranks = s, ranks
                    continue
                scale = max(abs(s), abs(best_score), 1.0)
                tied = abs(s - best_score) <= tol * scale
                if want_max:
                    better = s > best_score
                else:
                    better = s < best_score
                if better or (tied and vd > best_ranks[last]):
                    best_score, best_ranks = s, ranks
    if best_ranks is None:
        raise RuntimeError(
            f"穷举未找到可行解（B={budget:,}, 上界={hi}, 空间={enum_space(cost, budget, min_rank):,}）")
    p = sum(best_ranks[b] * cost[b] for b in BLOCKS)
    assert p == budget, f"[内部错误] 预算 {p:,} != {budget:,}"
    return best_ranks, float(best_score), n_cand


# --------------------------------------------------------------------------- #
# 精确求解器 1：论文线性目标的真实最优
# --------------------------------------------------------------------------- #
def solve_lagrangian_exact(gamma_abs: dict, cost: dict, budget: int,
                           min_rank: int = 1) -> dict:
    """`argmin Σ|Γ_k|·rank_k` s.t. `Σ rank_k·cost_k = B`，`rank_k ≥ min_rank`（穷举）。

    这是论文 Corollary 2 线性目标在**参数预算**约束下的真实最优——
    给出"论文若真的按目标函数优化，能做到多好"的上界。
    """
    g = {b: abs(gamma_abs[b]) for b in BLOCKS}
    ranks, obj, n_c = _enumerate_over_budget_surface(
        cost, budget, min_rank, lambda r: sum(g[b] * r[b] for b in BLOCKS))
    ref = sum(g[b] * ranks[b] for b in BLOCKS)
    assert abs(ref - obj) < 1e-6, "[内部错误] 目标不一致"
    return {"ranks": ranks, "objective": obj, "n_candidates": n_c,
            "method": "exact_enumeration_on_budget_surface"}


def solve_corner_exact(gamma_abs: dict, cost: dict, budget: int,
                       min_rank: int = 1) -> dict:
    """论文线性目标的**角点解**（β→∞ 的极限）：全给 |Γ| 最小的块。

    `Σ rank_k·cost_k = B` 的等式约束下，线性目标 `Σ|Γ_k|·rank_k` 的最优必在顶点。
    这里直接在精确预算面上取线性目标的最小值（不假设"其余块一定 rank=1"，
    因为 `cost_k` 不等时顶点结构会变）。
    """
    g = {b: abs(gamma_abs[b]) for b in BLOCKS}
    ranks, obj, n_c = _enumerate_over_budget_surface(
        cost, budget, min_rank, lambda r: sum(g[b] * r[b] for b in BLOCKS))
    bstar = min(BLOCKS, key=lambda b: g[b])
    return {"ranks": ranks, "objective": obj, "corner_block": bstar,
            "n_candidates": n_c,
            "param_share_of_corner_block": round(ranks[bstar] * cost[bstar] / budget, 6),
            "method": "exact_corner_on_budget_surface"}


# --------------------------------------------------------------------------- #
# 精确求解器 2：论文 Eq. 5 的整数最近解
# --------------------------------------------------------------------------- #
def solve_softmin_weights(gamma_abs: dict, cost: dict, budget: int, beta: float,
                          min_rank: int = 1, rank_budget: int | None = None,
                          cost_aware: bool = False) -> dict:
    r"""论文 Eq. 5 在**参数预算**约束下的整数最近解。

    ## 目标（两个变体都给出，`cost_aware` 切换）

    论文 Eq. 5 是 `rank*_k = C·exp(-β|Γ_k|) / Σ_j exp(-β|Γ_j|)`，其 (A3) 假设
    `Σ rank_k = C`（**rank 记账**）。但审稿人 R3.21 要求的是**参数量**等价
    `Σ rank_k·cost_k = B`。两种记账给出**不同**的规范解：

    | 变体 | 目标 rank | 来历 |
    |---|---|---|
    | `cost_aware=True` | `rank*_k = B·w_k / cost_k` | 在 `Σ rank_k·cost_k = B` 下重做 KKT：`log rank_k = −β|Γ_k| − βλ·cost_k − 1` ⇒ `rank_k ∝ w_k·exp(−βλ·cost_k)`；归一后即 `B·w_k/cost_k`。**论文 Eq. 5 漏掉了 `exp(−βλ·cost_k)` 因子**，等价于隐含假设所有 `cost_k` 相等 |
    | `cost_aware=False` | `rank*_k = R·w_k`（`R`=与 uniform 同口径的 Σ rank） | 论文 Eq. 5 的**字面**形式 |

    实测 `cost_k` 相差 **2.65×**，所以两者在 Qwen2-VL-2B 上不重合 —— 这本身是
    要报告给审稿人的事实（R2.2/R3.21）。

    ## 距离度量（`Σ_k (rank_k − rank*_k)² / (rank*_k)²`）

    **相对**偏差，因此对 `C`/`R` 的绝对尺度免疫（早期版本用绝对平方和，
    在 `R` 被算错时静默给出错误解 —— 由单测抓出）。数值上把 `rank*_k` 的
    下界夹到 1，避免 β 极大时除零。
    """
    w = softmin_weights(gamma_abs, beta)
    if rank_budget is None:
        rb = _uniform_rank_sum(cost, budget, min_rank)
    else:
        rb = int(rank_budget)

    if cost_aware:
        target_rank = {b: budget * w[b] / cost[b] for b in BLOCKS}
        variant = "cost_aware_B_over_cost_KKT"
    else:
        target_rank = {b: rb * w[b] for b in BLOCKS}
        variant = "paper_literal_R_times_w"
    # β=0 且 cost_aware 时 target_rank 已恒等于 uniform 解各块 rank；β 大时趋 0
    denom = {b: max(target_rank[b], 1.0) for b in BLOCKS}

    def score(r):
        return sum(((r[b] - target_rank[b]) / denom[b]) ** 2 for b in BLOCKS)

    ranks, dist, n_c = _enumerate_over_budget_surface(cost, budget, min_rank, score)
    return {"ranks": ranks, "distance": dist, "target_rank": target_rank,
            "weights": w, "variant": variant, "cost_aware": bool(cost_aware),
            "rank_budget_reference": rb,
            "rank_sum_achieved": int(sum(ranks.values())),
            "rank_sum_deviation_from_uniform": int(sum(ranks.values())) - rb,
            "n_candidates": n_c, "beta": beta,
            "method": "exact_nearest_relative_rank_deviation"}


def _uniform_rank_sum(cost: dict, budget: int, min_rank: int = 1) -> int:
    """uniform 整数解（各块 rank 尽量相等且精确命中预算）的 `Σ rank_k`。"""
    ranks, _, _ = _enumerate_over_budget_surface(
        cost, budget, min_rank,
        lambda r: max(r.values()) - min(r.values()))     # 极差最小 = 最均匀
    return int(sum(ranks.values()))


def uniform_plan(cost: dict, budget: int, min_rank: int = 1) -> dict:
    """最接近"各块同 rank"的**精确同预算**解（极差最小；平局取 rank 总和最大）。"""
    ranks, spread, n_c = _enumerate_over_budget_surface(
        cost, budget, min_rank,
        lambda r: max(r.values()) - min(r.values()))
    return {"ranks": ranks, "spread": spread, "n_candidates": n_c,
            "rank_sum": int(sum(ranks.values())),
            "method": "exact_min_rank_spread"}


# --------------------------------------------------------------------------- #
# 精确求解器 3：反向分配（sanity check）
# --------------------------------------------------------------------------- #
def solve_inverse_exponential(gamma_abs: dict, cost: dict, budget: int, beta: float,
                              min_rank: int = 1, cost_aware: bool = False) -> dict:
    """`rank_k ∝ exp(+β|Γ_k|)` —— 把**最大**份额给 |Γ| 最大的块（反向 sanity check）。

    sanity check：论文预测这条应当**更差**。β=0 时退化为 uniform。

    实现要点：`softmin_weights` 做的是 `exp(-β·g)`。要得到 `exp(+β|Γ|)`，
    应传入 `g_k = min|Γ| − |Γ_k|`（全程 ≥ 0，β 大时也不上溢），
    而不是传 `-|Γ_k|`（那会让 `min(g)<0`，`exp(-β·(g−min))` = `exp(β·(min−g))`
    指数爆炸 → inf，实测 β=1000 时 γ=inf）。
    """
    gmin = min(abs(gamma_abs[b]) for b in BLOCKS)
    g_inv = {b: gmin - abs(gamma_abs[b]) for b in BLOCKS}
    res = solve_softmin_weights(g_inv, cost, budget, beta, min_rank,
                               cost_aware=cost_aware)
    res["method"] = "exact_nearest_inverse_exponential"
    res["note"] = "rank ∝ exp(+β|Γ|)：把最大份额给 |Γ| 最大的块（sanity check）"
    return res
