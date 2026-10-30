# -*- coding: utf-8 -*-
r"""task-9 步骤 3：生成**逐块非均匀**分配方案，参数预算**逐位精确**对齐。

## 论文的分配律（`paper3/paper_ieee/sections/theory.tex` Eq. 5）

    rank*_k = C · exp(-beta |Gamma_k|) / sum_j exp(-beta |Gamma_j|)

**方向**：`exp(-β|Γ|)` ⇒ **|Γ| 越大的块 rank 越小** —— 在 alignment-sensitive
块上少给容量，把预算集中到 `|Γ|` 最小的块。Appendix D 称其为
"hard-protection configuration"。

## 记账口径（R3.21 的要害）

论文 (A3) 用 **rank 记账**（`Σ rank_k = C`）。但 LoRA 每 rank 参数成本

    cost_k = Σ_{Linear ∈ k} (in_features + out_features)

块间**不等**（Qwen2-VL-2B 实测：vision 655,360 vs shallow 247,296，**2.65×**）。
所以 **rank 均匀 ⇏ 参数均匀** —— 这正是 R3.21 问的
（"theory 组 r=4，random 组 {4,16,32,64}，如何保证有效参数预算等价？"）。

本脚本**一律按参数量记账**：所有方案在同一个 `B` 下满足
`Σ_k rank_k·cost_k == B`（**逐位相等**，不是"约等于"），并逐方案断言。

## 方案族（`Rank` = 逐块 rank）

| 方案 | 定义 | 作用 |
|---|---|---|
| `uniform` | 各块同 rank（论文现在 Theory 组的做法） | 主对照 |
| `exp_beta_*` | 论文 Eq. 5 的整数最近解（β 扫描 + ODE 拟合的 0.137） | **被验证对象** |
| `exp_ca_beta_*` | cost-aware 变体（`rank ∝ w_k/cost_k`，参数预算下的 KKT 解） | 稳健性对照 |
| `corner` | β→∞ 角点 = 线性目标真实最优 | 论文称 exp 族会退化成它 |
| `inverse_beta_*` | `rank ∝ exp(+β|Γ|)`（**反序**） | sanity check：应当更差 |
| `random_*` | 从**精确同预算可行集**里随机抽 | 零假设 |
| `exact_opt` | `min Σ|Γ_k|·rank_k` s.t. 同预算（穷举） | 理想上界 |

## 用法

    python tools\_p438_alloc_plans.py --apply
"""
from __future__ import annotations

import io
import json
import random
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_alloc_solvers import (BLOCKS, enum_space, is_feasible,  # noqa: E402
                                 rank_bounds, solve_corner_exact,
                                 solve_inverse_exponential,
                                 solve_lagrangian_exact, solve_softmin_weights,
                                 uniform_plan)

PROBE = REPO / "outputs" / "analysis" / "p3_alloc_budget_probe.json"
GAMMA = REPO / "outputs" / "analysis" / "p3_alloc_gamma_qwen2vl2b.json"
ODE_LEDGER = REPO / "outputs" / "analysis" / "ode_ledger.json"
OUT = REPO / "outputs" / "analysis" / "p3_alloc_plans.json"

UNIFORM_R = 4          # 论文 Theory 组的同预算口径（= uniform r=4）
N_RANDOM = 20
MIN_RANK = 1

BETA_GRID = {
    "beta_0": 0.0,
    "beta_1e-6": 1e-6,
    "beta_1e-4": 1e-4,
    "beta_3e-4": 3e-4,
    "beta_paper_0.137": 0.137,
    "beta_1e3": 1e3,
    "beta_1e9": 1e9,
}


def params_of(ranks, cost):
    return sum(ranks[b] * cost[b] for b in BLOCKS)


def exact_budget_set(cost, budget, min_rank=MIN_RANK, cap=200000):
    """列出**所有**精确命中预算的整数分配（自由度 = 该预算可选方案数）。"""
    hi = rank_bounds(cost, budget, min_rank)
    last = min(BLOCKS, key=lambda b: cost[b])
    outer = [b for b in BLOCKS if b != last]
    a, b_, c = outer
    out = []
    for va in range(min_rank, hi[a] + 1):
        for vb in range(min_rank, hi[b_] + 1):
            for vc in range(min_rank, hi[c] + 1):
                num = budget - (va * cost[a] + vb * cost[b_] + vc * cost[c])
                if num < 0 or num % cost[last]:
                    continue
                vd = num // cost[last]
                if vd < min_rank or vd > hi[last]:
                    continue
                out.append({a: va, b_: vb, c: vc, last: vd})
                if len(out) >= cap:
                    return out, hi, True
    return out, hi, False


def main() -> int:
    if "--apply" not in sys.argv:
        print("=== 分配方案规划（预演）===")
        print(f"  预算 = uniform r={UNIFORM_R}（论文 Theory 组同预算）")
        print("  --apply 实跑")
        return 0

    for p in (PROBE, GAMMA, ODE_LEDGER):
        if not p.exists():
            print(f"[FATAL] 缺 {p.relative_to(REPO)} —— 先跑前置脚本")
            return 1
    probe = json.loads(io.open(PROBE, encoding="utf-8").read())
    gd = json.loads(io.open(GAMMA, encoding="utf-8").read())
    ledger = json.loads(io.open(ODE_LEDGER, encoding="utf-8").read())

    cost = {b: int(probe["per_block"][b]["cost_per_rank"]) for b in BLOCKS}
    gamma = {b: float(gd["gamma_final"][b]) for b in BLOCKS}
    gabs = {b: abs(gamma[b]) for b in BLOCKS}
    budget = UNIFORM_R * sum(cost.values())

    print("实测 Γ_k（Qwen2-VL-2B，脚本 tools/_p432_gamma_blocks.py）:")
    for b in BLOCKS:
        print(f"  {b:<12} Γ={gamma[b]:+.6e}  |Γ|={gabs[b]:.6e}")
    print(f"\n预算 B = {UNIFORM_R} × Σcost = {budget:,}")
    ok, why = is_feasible(cost, budget, MIN_RANK)
    print(f"可行性: {ok} {why}")

    all_allocs, hi, truncated = exact_budget_set(cost, budget)
    print(f"该预算下**精确同参数**的分配方案数 = {len(all_allocs)}{'+' if truncated else ''}"
          f"｜rank 上界 {hi}｜枚举空间 {enum_space(cost, budget):,}")

    sigma = st.stdev([gabs[b] for b in BLOCKS])
    beta_star = 1.0 / sigma
    ode_betas = [r["beta"] for r in ledger["runs"]
                 if isinstance(r.get("beta"), (int, float))]
    print(f"\n|Γ| 离散度 sd={sigma:.4e}｜max/min={max(gabs.values()) / min(gabs.values()):.2f}"
          f"｜β*=1/sd={beta_star:.3e}")
    print(f"ODE ledger β（n={len(ode_betas)}）median={st.median(ode_betas):.6f}"
          f"｜正文所用 0.137 的出处 = runs[90].beta = {ledger['runs'][90]['beta']!r}"
          f"（conf={ledger['runs'][90].get('conf')!r}）")

    plans: dict[str, dict] = {}

    # 1) uniform（论文现在的 Theory 组）
    uni = uniform_plan(cost, budget, MIN_RANK)
    plans["uniform"] = {"family": "uniform",
                        "ranks": uni["ranks"],
                        "note": "论文 Theory 组现在的做法：各块同 rank（rank 均匀）"}

    # 2) 论文 Eq. 5 的整数最近解（β 扫描）
    for name, beta in BETA_GRID.items():
        try:
            r = solve_softmin_weights(gabs, cost, budget, beta)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] exp_{name} 不可解: {exc}")
            continue
        plans[f"exp_{name}"] = {
            "family": "exponential_eq5_literal", "beta": beta,
            "ranks": r["ranks"], "lattice_distance": r["distance"],
            "target_rank": r["target_rank"], "softmin_weights": r["weights"],
            "n_candidates": r["n_candidates"],
        }

    # 3) cost-aware 变体（稳健性对照）
    for name, beta in (("beta_paper_0.137", 0.137), ("beta_1e-4", 1e-4),
                       ("beta_1e9", 1e9)):
        r = solve_softmin_weights(gabs, cost, budget, beta, cost_aware=True)
        plans[f"exp_ca_{name}"] = {
            "family": "exponential_eq5_cost_aware", "beta": beta,
            "ranks": r["ranks"], "lattice_distance": r["distance"],
            "n_candidates": r["n_candidates"],
        }

    # 4) 反序（sanity check）
    for name, beta in (("beta_paper_0.137", 0.137), ("beta_1e-4", 1e-4),
                       ("beta_1e9", 1e9)):
        r = solve_inverse_exponential(gabs, cost, budget, beta)
        plans[f"inverse_{name}"] = {
            "family": "inverse_exponential_sanity_check", "beta": beta,
            "ranks": r["ranks"], "lattice_distance": r["distance"],
            "n_candidates": r["n_candidates"]}

    # 5) 真最优 & 角点
    opt = solve_lagrangian_exact(gabs, cost, budget, MIN_RANK)
    plans["exact_opt"] = {"family": "linear_objective_true_optimum",
                          "ranks": opt["ranks"],
                          "linear_objective": opt["objective"],
                          "n_candidates": opt["n_candidates"]}
    corner = solve_corner_exact(gabs, cost, budget, MIN_RANK)
    plans["corner"] = {"family": "corner_beta_inf",
                       "ranks": corner["ranks"],
                       "linear_objective": corner["objective"],
                       "corner_block": corner["corner_block"],
                       "param_share_of_corner_block":
                           corner["param_share_of_corner_block"]}
    print(f"\n角点解把最多参数给 {corner['corner_block']}"
          f"（占预算 {corner['param_share_of_corner_block']:.1%}）")

    # 6) random（从精确可行集里抽，保证预算逐位相等）
    rng = random.Random(20261012)
    pool = list(all_allocs)
    rng.shuffle(pool)
    n_rand = 0
    for a in pool:
        if n_rand >= N_RANDOM:
            break
        if a == plans["uniform"]["ranks"]:
            continue
        plans[f"random_{n_rand:02d}"] = {"family": "random_same_budget",
                                         "ranks": dict(a),
                                         "sampled_from_exact_budget_set": True}
        n_rand += 1
    print(f"random 方案取自精确可行集（{len(all_allocs)} 个）中的 {n_rand} 个")

    # ---- 硬断言：每个方案逐位精确命中预算 ----
    print("\n=== 预算对齐硬断言（逐位相等）===")
    bad = []
    for name, p in plans.items():
        ntp = params_of(p["ranks"], cost)
        p["n_trainable_params"] = ntp
        p["budget_exact_match"] = (ntp == budget)
        p["linear_objective"] = sum(gabs[b] * p["ranks"][b] for b in BLOCKS)
        p["param_share"] = {b: p["ranks"][b] * cost[b] / budget for b in BLOCKS}
        p["rank_sum"] = int(sum(p["ranks"].values()))
        if ntp != budget:
            bad.append((name, ntp))
    for name in sorted(plans):
        p = plans[name]
        flag = "OK " if p["budget_exact_match"] else "FAIL"
        print(f"  {flag} {name:<26} { {b: p['ranks'][b] for b in BLOCKS} } "
              f"params={p['n_trainable_params']:,}")
    if bad:
        print(f"\n  [FATAL] 未精确命中预算: {bad}")
        return 1

    uni_obj = plans["uniform"]["linear_objective"]
    print("\n=== 线性目标 Σ|Γ_k|·rank_k（论文认为越小越好）===")
    for name in sorted(plans, key=lambda n: plans[n]["linear_objective"]):
        o = plans[name]["linear_objective"]
        rel = (uni_obj / o - 1) * 100 if o > 0 else float("nan")
        print(f"  {name:<26} obj={o:>16,.0f}  vs uniform {'+' if rel >= 0 else ''}{rel:.1f}%")

    rec = {
        "script": "tools/_p438_alloc_plans.py",
        "model": "models/Qwen2-VL-2B-Instruct",
        "blocks": BLOCKS,
        "gamma_source": "outputs/analysis/p3_alloc_gamma_qwen2vl2b.json :: gamma_final",
        "cost_source": "outputs/analysis/p3_alloc_budget_probe.json "
                       ":: per_block[*].cost_per_rank",
        "budget_params": budget,
        "budget_derivation": f"uniform rank {UNIFORM_R} × Σ_k cost_k = {budget:,}"
                             "（= 论文 Theory 组同预算；按**参数量**记账）",
        "uniform_rank": UNIFORM_R,
        "rank_upper_bounds": hi,
        "enum_space": enum_space(cost, budget),
        "n_exact_budget_allocations": len(all_allocs),
        "exact_budget_allocations_truncated": truncated,
        "exact_budget_allocations": all_allocs,
        "cost_per_rank": cost,
        "gamma_measured": gamma,
        "gamma_abs": gabs,
        "gamma_separation": {"sd_abs": sigma,
                             "mean_abs": sum(gabs.values()) / len(BLOCKS),
                             "max_min_ratio": max(gabs.values()) / min(gabs.values())},
        "beta_star_1_over_sigma": beta_star,
        "beta_grid": BETA_GRID,
        "ode_ledger_beta": {
            "source": "outputs/analysis/ode_ledger.json :: runs[*].beta",
            "n": len(ode_betas), "median": st.median(ode_betas),
            "min": min(ode_betas), "max": max(ode_betas),
            "paper_value_0.137_provenance":
                f"outputs/analysis/ode_ledger.json :: runs[90].beta = "
                f"{ledger['runs'][90]['beta']!r} "
                f"(conf={ledger['runs'][90].get('conf')!r}, "
                f"family={ledger['runs'][90].get('family')!r})",
        },
        "plans": plans,
        "hard_assert_all_plans_exact_budget": not bad,
        "n_plans": len(plans),
        "uniform_linear_objective": uni_obj,
        "exact_opt_linear_objective": plans["exact_opt"]["linear_objective"],
        "corner_linear_objective": plans["corner"]["linear_objective"],
        "key_fact_rank_uniform_neq_param_uniform":
            "uniform 解各块 rank 相等，但逐块参数量为 "
            f"{ {b: plans['uniform']['ranks'][b] * cost[b] for b in BLOCKS} } —— "
            "相差 %.2f×（cost_k 块间不等）" % (
                max(plans['uniform']['ranks'][b] * cost[b] for b in BLOCKS)
                / min(plans['uniform']['ranks'][b] * cost[b] for b in BLOCKS)),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"\n已写 {OUT.relative_to(REPO)}（{len(plans)} 方案，全部精确同预算 {budget:,}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
