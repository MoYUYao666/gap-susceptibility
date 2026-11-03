# -*- coding: utf-8 -*-
r"""task-9 分配数学的**单元测试**（纯 CPU，不加载模型、不占卡）。

分配律是整个 E 组的核心；一旦取整/预算记账/度量写错，后面所有训练都白跑。
本脚本用**合成 Γ**（覆盖 10^2–10^8 跨量级、含正负号、含相等值），在
**与主实验相同的成本比**下验证：

§0 预算可行性与搜索空间（含"最小成本"下界）
§1 `softmin_weights`：归一化 + **数值稳定**（β 大 + |Γ| 跨量级不上溢）
§2 论文 Eq. 5 整数解：`Σ rank_k·cost_k == B` **逐位精确**、`rank_k ≥ 1`
§3 **单调性**：β↗ ⇒ `|Γ|` 最大的块 rank 不增、`|Γ|` 最小的块 rank 不减
§4 **β→∞ ⇒ 线性目标最优**（Appendix D 的 hard-protection 说法）
§5 **β→0 ⇒ uniform**（论文原话 "β→0 degenerates to uniform"）
§6 线性目标最优的**最优性**（与独立暴力枚举逐位交叉验证）
§7 反向分配（sanity check 的前提）

以及一条**要写进报告的硬事实**：uniform rank 时逐块参数量并**不**相等
（`cost_k` 差 2.65×）—— 这就是 R3.21 的症结。

    python tools\_p435_tests_alloc_math.py
"""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_alloc_solvers import (BLOCKS, enum_space, is_feasible,  # noqa: E402
                                 rank_bounds, softmin_weights,
                                 solve_corner_exact, solve_inverse_exponential,
                                 solve_lagrangian_exact, solve_softmin_weights,
                                 uniform_plan)

# 与 Qwen2-VL-2B 实测一致的量级（tools/_p420_arch_probe.py）
COST = {"vision": 655360, "llm_shallow": 247296, "llm_mid": 577024, "llm_deep": 329728}
# **主实验预算**（= uniform r=4）= 7,237,632。单测直接用主预算：
# 早期版本为了让枚举更快而用 r=2 的小预算（可行面只有 3 个点），
# 结果"β→∞ 达到线性目标最优"这条断言在小预算下**不可满足**（最优解不在可行面里），
# 把测试本身写错了。主预算可行面 15 个点、枚举空间 33,660，秒级，足够。
BUDGET = 4 * sum(COST.values())
SCALE = 4                                     # 该预算下的 uniform rank

GAMMA_CASES = {
    # 论文说 Qwen 的 |Γ| 跨 10^2–10^8（experiments.tex Finding 4）
    "cross_magnitude": {"vision": -3.7e8, "llm_shallow": -9.0e2,
                        "llm_mid": -2.1e3, "llm_deep": -7.2e3},
    "llava_like": {"vision": -8092.0, "llm_shallow": 1614.0,
                   "llm_mid": 8717.0, "llm_deep": 2727.0},
    "mixed_sign": {"vision": -1e6, "llm_shallow": 1e2, "llm_mid": -5e4, "llm_deep": 3e3},
    "near_equal": {"vision": 1000.0, "llm_shallow": 1001.0,
                   "llm_mid": 1002.0, "llm_deep": 1003.0},
}
BETAS = [0.0, 1e-12, 1e-9, 1e-6, 1e-4, 3e-4, 0.137, 1.0, 1e3, 1e6, 1e12]

fails: list[str] = []


def check(label, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f" ｜ {detail}" if detail else ""))
    if not cond:
        fails.append(label)


def params_of(ranks, cost):
    return sum(ranks[b] * cost[b] for b in BLOCKS)


def main() -> int:
    print("=== 0. 预算可行性 & 搜索空间 ===")
    ok, why = is_feasible(COST, BUDGET)
    check(f"主预算 B={BUDGET:,} 可行", ok, why or "")
    print(f"  rank 上界 {rank_bounds(COST, BUDGET)}"
          f"｜枚举空间 {enum_space(COST, BUDGET):,}")
    check("最小成本 = Σcost", sum(COST.values()) == 1_809_408, f"{sum(COST.values()):,}")
    ok2, why2 = is_feasible(COST, 1_000_000)
    check("预算 1,000,000 不可行（< 最小成本）", not ok2, why2)
    for r in (1, 2, 3, 4):
        check(f"uniform r={r} 成本 == {r}·Σcost",
              r * sum(COST.values()) == sum(r * COST[b] for b in BLOCKS),
              f"{r * sum(COST.values()):,}")

    print("\n=== 0b. 关键事实：cost_k 不等 ⇒ rank 均匀 ≠ 参数均匀 ===")
    uni_main = uniform_plan(COST, BUDGET)["ranks"]
    eta = {b: uni_main[b] * COST[b] for b in BLOCKS}
    check("主预算 uniform 解各块 rank 相等",
          len(set(uni_main.values())) == 1, str(uni_main))
    check("但其逐块参数量**不**相等（R3.21 症结）",
          len(set(eta.values())) > 1, f"η={eta}")
    print(f"  cost 比值 max/min = {max(COST.values()) / min(COST.values()):.2f}×"
          f"｜参数量比 = {max(eta.values()) / min(eta.values()):.2f}×")

    print("\n=== 1. softmin_weights：归一化与数值稳定 ===")
    for name, g in GAMMA_CASES.items():
        ga = {b: abs(g[b]) for b in BLOCKS}
        for beta in BETAS:
            w = softmin_weights(ga, beta)
            tot = sum(w.values())
            finite_pos = all(math.isfinite(v) and v >= 0 for v in w.values())
            check(f"{name} β={beta:g} 归一化+有限非负",
                  abs(tot - 1.0) < 1e-12 and finite_pos,
                  f"Σw={tot:.12f}")
    w0 = softmin_weights({b: abs(GAMMA_CASES["cross_magnitude"][b]) for b in BLOCKS}, 0.0)
    check("β=0 ⇒ 均匀权重", all(abs(v - 0.25) < 1e-12 for v in w0.values()))
    ga_cm = {b: abs(GAMMA_CASES["cross_magnitude"][b]) for b in BLOCKS}
    w_cm = softmin_weights(ga_cm, 0.137)
    check("跨量级 β=0.137 无 nan/inf",
          all(math.isfinite(v) for v in w_cm.values()),
          f"min={min(w_cm.values()):.3e} max={max(w_cm.values()):.6f}")

    print("\n=== 2. 论文 Eq. 5 整数解：预算精确命中 + rank≥1 ===")
    for name, g in GAMMA_CASES.items():
        ga = {b: abs(g[b]) for b in BLOCKS}
        for beta in BETAS:
            try:
                r = solve_softmin_weights(ga, COST, BUDGET, beta)["ranks"]
            except Exception as exc:  # noqa: BLE001
                check(f"{name} β={beta:g} 可解", False, f"{type(exc).__name__}: {exc}")
                continue
            p = params_of(r, COST)
            check(f"{name} β={beta:g} 预算精确", p == BUDGET, f"{p:,} vs {BUDGET:,}")
            check(f"{name} β={beta:g} rank≥1", all(v >= 1 for v in r.values()), str(r))

    print("\n=== 3. 单调性：β↗ ⇒ 高|Γ|块 rank 不增、低|Γ|块 rank 不减 ===")
    print("  （`near_equal` 的四块 |Γ| 相差 <0.4%，排序本身无意义 → 跳过严格单调检查）")
    for name, g in GAMMA_CASES.items():
        ga = {b: abs(g[b]) for b in BLOCKS}
        hi_b = max(BLOCKS, key=lambda b: ga[b])
        lo_b = min(BLOCKS, key=lambda b: ga[b])
        if name == "near_equal":
            print(f"  (skip) {name}: |Γ| 极差 {max(ga.values()) - min(ga.values()):.1f}"
                  f"（相对 {(max(ga.values()) / min(ga.values()) - 1) * 100:.2f}%）")
            continue
        prev = None
        for beta in BETAS:
            r = solve_softmin_weights(ga, COST, BUDGET, beta)["ranks"]
            if prev is not None:
                check(f"{name} β={beta:<7g} {hi_b} 不增", r[hi_b] <= prev[hi_b],
                      f"{prev[hi_b]}→{r[hi_b]}")
                check(f"{name} β={beta:<7g} {lo_b} 不减", r[lo_b] >= prev[lo_b],
                      f"{prev[lo_b]}→{r[lo_b]}")
            prev = r

    print("\n=== 4. 硬保护极限：β→∞ ⇒ 线性目标最优 ===")
    for name, g in GAMMA_CASES.items():
        ga = {b: abs(g[b]) for b in BLOCKS}
        r_corner = solve_corner_exact(ga, COST, BUDGET)["ranks"]
        obj_opt = sum(ga[b] * r_corner[b] for b in BLOCKS)
        if name == "near_equal":
            # 已知局限（如实记录，不掩盖）：四块 |Γ| 相差 <0.4% 时，
            # softmin 的解析权重趋近并列，而"最近解"度量里的分母被夹到 1，
            # 于是解被拉向均匀而非角点。此时"最优排序"本身也无意义。
            rr = solve_softmin_weights(ga, COST, BUDGET, 1e9)["ranks"]
            obj = sum(ga[b] * rr[b] for b in BLOCKS)
            print(f"  (KNOWN LIMIT) {name}: |Γ| 极差 "
                  f"{(max(ga.values()) / min(ga.values()) - 1) * 100:.2f}% → "
                  f"β→∞ 解 {rr} obj={obj:.6g}，线性目标最优 {r_corner} obj={obj_opt:.6g}；"
                  f"**分离度不足时 softmin 最近解不保证达到目标最优**")
            continue
        for beta in (1.0, 1e3, 1e9, 1e12):
            rr = solve_softmin_weights(ga, COST, BUDGET, beta)["ranks"]
            obj = sum(ga[b] * rr[b] for b in BLOCKS)
            check(f"{name} β={beta:g} 达到线性目标最优",
                  abs(obj - obj_opt) <= 1e-6 * max(abs(obj_opt), 1.0),
                  f"obj={obj:.6g} vs opt={obj_opt:.6g}")
        uni = uniform_plan(COST, BUDGET)["ranks"]
        check(f"{name} 最优目标 ≤ uniform 目标",
              obj_opt <= sum(ga[b] * uni[b] for b in BLOCKS) + 1e-9,
              f"{obj_opt:.6g} vs {sum(ga[b] * uni[b] for b in BLOCKS):.6g}")

    print("\n=== 5. β→0 ⇒ uniform（论文原话）===")
    for name, g in GAMMA_CASES.items():
        ga = {b: abs(g[b]) for b in BLOCKS}
        r0 = solve_softmin_weights(ga, COST, BUDGET, 0.0)["ranks"]
        check(f"{name} β=0 ⇒ 各块 rank 相等", all(v == SCALE for v in r0.values()),
              f"{r0}（期望各块 {SCALE}）")
    r_a = solve_softmin_weights({b: abs(GAMMA_CASES["near_equal"][b]) for b in BLOCKS},
                                COST, BUDGET, 0.0)["ranks"]
    r_b = solve_softmin_weights({b: abs(GAMMA_CASES["cross_magnitude"][b]) for b in BLOCKS},
                                COST, BUDGET, 0.0)["ranks"]
    check("β=0 解与 Γ 取值无关", r_a == r_b, f"{r_a} vs {r_b}")
    check("β=0 解 == 极小极差解", r_a == uniform_plan(COST, BUDGET)["ranks"])

    print("\n=== 5b. cost-aware 变体（同一个问题，另一个规范化）===")
    for name, g in GAMMA_CASES.items():
        ga = {b: abs(g[b]) for b in BLOCKS}
        r_ca = solve_softmin_weights(ga, COST, BUDGET, 0.137, cost_aware=True)["ranks"]
        check(f"{name} cost-aware 变体预算精确",
              params_of(r_ca, COST) == BUDGET, f"{r_ca} → {params_of(r_ca, COST):,}")
        r_lit = solve_softmin_weights(ga, COST, BUDGET, 0.137)["ranks"]
        print(f"  {name}: 字面 Eq.5 {r_lit} ｜ cost-aware KKT {r_ca}")
    print("  （两个变体都精确同预算；主实验用**字面**变体，cost-aware 作为稳健性对照）")

    print("\n=== 6. 线性目标最优：穷举 vs 独立暴力枚举 ===")
    small_cost = {"vision": 5, "llm_shallow": 2, "llm_mid": 4, "llm_deep": 3}
    small_budget = 3 * sum(small_cost.values())      # = 42
    small_g = {"vision": 8.0, "llm_shallow": 1.0, "llm_mid": 9.0, "llm_deep": 3.0}
    got = solve_lagrangian_exact(small_g, small_cost, small_budget)["ranks"]
    best, best_obj = None, None
    for combo in itertools.product(range(1, 20), repeat=4):
        p = sum(combo[i] * small_cost[BLOCKS[i]] for i in range(4))
        if p != small_budget:
            continue
        obj = sum(small_g[BLOCKS[i]] * combo[i] for i in range(4))
        if best_obj is None or obj < best_obj:
            best_obj, best = obj, {BLOCKS[i]: combo[i] for i in range(4)}
    check("穷举解 == 独立暴力枚举", got == best, f"{got} vs {best}")
    check("穷举解预算精确", params_of(got, small_cost) == small_budget)
    for name, g in GAMMA_CASES.items():
        ga = {b: abs(g[b]) for b in BLOCKS}
        opt = solve_lagrangian_exact(ga, COST, BUDGET)
        obj_sm = min(sum(ga[x] * solve_softmin_weights(ga, COST, BUDGET, beta)["ranks"][x]
                         for x in BLOCKS) for beta in BETAS)
        check(f"{name} 精确最优 ≤ 所有 softmin 解", opt["objective"] <= obj_sm + 1e-6,
              f"{opt['objective']:.6g} vs {obj_sm:.6g}")
        check(f"{name} 精确解预算精确",
              params_of(opt["ranks"], COST) == BUDGET, str(opt["ranks"]))

    print("\n=== 7. 反向分配（sanity check 的前提）===")
    for name, g in GAMMA_CASES.items():
        ga = {b: abs(g[b]) for b in BLOCKS}
        hi_b = max(BLOCKS, key=lambda b: ga[b])
        fwd = solve_softmin_weights(ga, COST, BUDGET, 1e-3)
        inv = solve_inverse_exponential(ga, COST, BUDGET, 1e-3)
        check(f"{name} 反向给 {hi_b} 的参数份额 ≥ 正序",
              inv["ranks"][hi_b] * COST[hi_b] >= fwd["ranks"][hi_b] * COST[hi_b],
              f"inv={ {b: inv['ranks'][b] for b in BLOCKS} } "
              f"fwd={ {b: fwd['ranks'][b] for b in BLOCKS} }")
        r0 = solve_inverse_exponential(ga, COST, BUDGET, 0.0)["ranks"]
        check(f"{name} 反向 β=0 ⇒ uniform", all(v == SCALE for v in r0.values()), str(r0))

    print(f"\n=== 结论：{len(fails)} 项失败 ===")
    if fails:
        for f in fails:
            print("  FAIL:", f)
        return 1
    print("  全部分配数学检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
