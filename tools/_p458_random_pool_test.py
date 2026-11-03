# -*- coding: utf-8 -*-
r"""task-9 补充：**随机对照臂的池化比较**（预先写定判据，避免事后挑结论）。

## 背景

第一轮主实验（5 方案 × 3 seed）里"随机"只有 **1 个抽样**（`random_00`，均值 +1103），
而它的均值**低于** Γ-guided（+2241）。Lead 要求补 `random_01/02/03`，并**预先**给出
两种可能的稿件表述，按实测二选一：

- 若多个随机方案的均值**仍显著低于** Γ-guided → "**Γ-guided 不优于同预算随机分配**"
- 若随机方案**散布很大、Γ-guided 落在其上分位** → "**不可区分，但方差更小**"

## 本脚本的判据（**先写死，再看数**）

把所有 `random_*` 方案的 run **池化**成"同预算随机分配"的经验分布（n = 3 × 方案数），
然后：

| 检验 | 统计量 | 判读 |
|---|---|---|
| **位置** | Welch t（Γ-guided vs 随机池） | p < 0.05 且 Γ-guided 均值**更高** ⇒ "不优于随机"；否则"不可区分" |
| **位置（非参）** | Mann-Whitney U（小样本更稳） | 同上，作为 Welch 的稳健性对照 |
| **经验分位** | Γ-guided 均值在随机池 12 个 run 中的百分位 | > 75% ⇒ 落在上分位（更差） |
| **方差** | Levene / F 检验（Γ-guided vs 随机池） | Γ-guided 方差**显著更小** ⇒ 才可写"方差更小" |

**结论只能是下面四者之一**（脚本自动判定并打印，避免我手工挑选）：
1. `GAMMA_NOT_BETTER_THAN_RANDOM`（随机池显著更好）
2. `INDISTINGUISHABLE_BUT_LOWER_VARIANCE`（位置不可区分 + 方差显著更小）
3. `UNDERPOWERED_TO_DISTINGUISH`（**功效不足**：同分配内的 seed 极差 ≥ 方案间差异）
4. `INDISTINGUISHABLE`（以上都不成立）

**第 3 档的来历**（Lead 2026-10-13 提出，比强行在三档里选一个更诚实）：
`random_01` 同分配内 seed 极差 = **10,912.9**（+839.0 vs +11,751.8），
而 `exp`(+2241) vs `uniform`(+6413) 的方案间差异只有 **4,172** —— **同分配内噪声是方案间差异的 2.6×**
⇒ 此时任何"方案间"的 p 值都不可靠，**必须显式判为功效不足**，而不是报一个好看的 p。

    python tools\_p458_random_pool_test.py --apply
"""
from __future__ import annotations

import io
import json
import math
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

PLANS = REPO / "outputs" / "analysis" / "p3_alloc_plans.json"
RUNDIR = REPO / "outputs" / "analysis" / "p3_alloc_runs"
OUT = REPO / "outputs" / "analysis" / "p3_alloc_random_pool.json"

GAMMA_PLAN = "exp_beta_paper_0.137"


def welch(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan"), float("nan")
    se2 = st.variance(a) / na + st.variance(b) / nb
    if se2 <= 0:
        return float("nan"), float("nan")
    t = (st.mean(a) - st.mean(b)) / math.sqrt(se2)
    df = se2 ** 2 / ((st.variance(a) / na) ** 2 / (na - 1)
                     + (st.variance(b) / nb) ** 2 / (nb - 1))
    try:
        from scipy import stats
        p = float(2 * stats.t.sf(abs(t), df))
    except Exception:  # noqa: BLE001
        p = float("nan")
    return float(t), p


def mannwhitney(a, b):
    try:
        from scipy import stats
        u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        return float(u), float(p)
    except Exception:  # noqa: BLE001
        return float("nan"), float("nan")


def levene(a, b):
    try:
        from scipy import stats
        w, p = stats.levene(a, b, center="median")
        return float(w), float(p)
    except Exception:  # noqa: BLE001
        return float("nan"), float("nan")


def load_runs():
    runs = {}
    for tagdir in sorted(p for p in RUNDIR.iterdir() if p.is_dir()):
        for f in tagdir.glob("*.json"):
            if f.name in ("summary.json", "adalora_summary.json"):
                continue
            try:
                r = json.loads(io.open(f, encoding="utf-8").read())
            except Exception:  # noqa: BLE001
                continue
            if r.get("ok") and r.get("delta_E") is not None:
                runs[f.stem] = r
    return runs


def main() -> int:
    if "--apply" not in sys.argv:
        print("=== 随机池化比较（预演）===")
        print("  判据已写死在脚本 docstring：位置检验 + 经验分位 + 方差检验")
        return 0

    plans = json.loads(io.open(PLANS, encoding="utf-8").read())
    runs = load_runs()
    print(f"读到 {len(runs)} 个成功 run")

    # ---- 排除与**规则方案解重合**的随机抽样（重复计数，且会污染判据）----
    #
    # 为什么必须排除（Lead 2026-10-13 发现）：同预算可行集**只有 15 个**不同分配，
    # 而 `random_*` 是在这个离散面上抽的，于是有 4 个恰好落在规则解上：
    #   random_00 = exp_ca_beta_1e-4 （**cost-aware 的 Γ 规则变体**，β=1e-4）
    #   random_04 = corner
    #   random_12 = inverse_beta_paper_0.137
    #   random_13 = exp_beta_paper_0.137（**论文 Eq.5 本身的解**）
    # ⇒ 尤其 `random_00`：它的 +1103 曾被我读成"随机分配最低"，但它是**一条 Γ 规则**，
    #    **不是独立随机抽样** ⇒ "Γ-guided 未胜随机"这条判据被污染，必须剔除后重算。
    KNOWN_RULE_SOLUTIONS = {
        "random_00": "exp_ca_beta_1e-4",
        "random_04": "corner",
        "random_12": "inverse_beta_paper_0.137",
        "random_13": "exp_beta_paper_0.137",
    }
    rand_all = sorted(k for k in plans["plans"] if k.startswith("random_"))
    dup = {n: KNOWN_RULE_SOLUTIONS[n] for n in rand_all if n in KNOWN_RULE_SOLUTIONS}
    # 独立复核：用 rank 向量再验一遍，防止上面这张表写错
    def _rk(n):
        return tuple(plans["plans"][n]["ranks"][b] for b in plans["blocks"])
    for n, ref in list(dup.items()):
        if ref in plans["plans"] and _rk(n) != _rk(ref):
            print(f"[warn] {n} 与 {ref} 的 rank 向量**不一致**，仍按重复处理，请人工复核")
    rand_plans = [n for n in rand_all if n not in dup]
    print(f"全部随机方案 {len(rand_all)} 个｜与规则解重合（排除）{len(dup)} 个：{dup}")
    print(f"**独立随机样本** {len(rand_plans)} 个：{rand_plans}")

    def vals(plan):
        return [r["delta_E"] for k, r in runs.items() if r.get("plan") == plan]

    gamma = vals(GAMMA_PLAN)
    pool, per_plan = [], {}
    for n in rand_plans:
        v = vals(n)
        if not v:
            continue          # 该随机方案尚未跑：不进池、不打印（避免"n=0"噪声）
        per_plan[n] = {"n": len(v), "mean": st.mean(v),
                       "sd": st.stdev(v) if len(v) > 1 else 0.0,
                       "ranks": plans["plans"][n]["ranks"],
                       "linear_objective": plans["plans"][n]["linear_objective"]}
        pool += v
    not_yet = [n for n in rand_plans if n not in per_plan]
    if not_yet:
        print(f"（尚未跑、未计入池：{not_yet}）")
    if not gamma or len(pool) < 2:
        # 允许 n=2 的**部分**诊断（便于 P1 进行中观察功效趋势）；正式判定仍需更多
        print("[WAIT] 数据不足（Γ-guided 或随机池的 run 太少）—— "
              "正式判定需随机池 ≥ 5 个 run；当前仅够看功效趋势")
        return 0
    partial = len(pool) < 5

    print(f"\nΓ-guided（{GAMMA_PLAN}）: n={len(gamma)} mean={st.mean(gamma):+.1f} "
          f"sd={st.stdev(gamma):.1f}")
    print(f"随机池（{len(per_plan)} 个已跑方案池化）: n={len(pool)} mean={st.mean(pool):+.1f} "
          f"sd={st.stdev(pool):.1f}")
    for n, d in per_plan.items():
        m = "n/a" if d["mean"] is None else f"{d['mean']:+.1f}"
        s = "n/a" if d["sd"] is None else f"{d['sd']:.1f}"
        print(f"  {n:<12} n={d['n']} mean={m} sd={s} ranks={d['ranks']}")

    t, p_t = welch(gamma, pool)
    u, p_u = mannwhitney(gamma, pool)
    w, p_w = levene(gamma, pool)

    # ---- 方差的**分解**（Lead 预先写定的口径，2026-10-13）----
    #
    # 关键：随机池 sd 是**混合量**（10 个方案 × 3 seed ⇒ 同时含组间与组内），
    # 而 Γ-guided 的 sd 是**单一方案的组内 sd**。**两者不是同一个量，直接比大小没有意义。**
    # 故这里显式拆开：
    #   between_sd  = 10 个**方案均值**之间的 sd（该比的量）
    #   within_sd   = 每个方案内 seed sd 的**中位数**（典型组内噪声）
    # 并把 Γ-guided 与"**组内残差池**"（每个 run 减去其所在方案均值后的偏差）做 Levene ——
    # 这才是"方差是否更小"的正确对照（而不是与含组间差异的混合池比）。
    arm_means = [d["mean"] for d in per_plan.values()]
    arm_sds = [d["sd"] for d in per_plan.values() if d["n"] > 1]
    between_sd = st.stdev(arm_means) if len(arm_means) > 1 else float("nan")
    within_sd_median = st.median(arm_sds) if arm_sds else float("nan")
    within_resid = []
    for n, d in per_plan.items():
        v = [r["delta_E"] for r in runs.values() if r.get("plan") == n]
        mu = st.mean(v)
        within_resid += [x - mu for x in v]
    w_in, p_in = levene(gamma, within_resid) if within_resid else (float("nan"), float("nan"))
    gamma_sd = st.stdev(gamma) if len(gamma) > 1 else float("nan")

    # 经验分位：Γ-guided 的均值在随机池单 run 分布中的百分位
    gm = st.mean(gamma)
    below = sum(1 for x in pool if x < gm)
    pct = below / len(pool) * 100

    # 结论判定（写死的规则）
    gamma_worse = (st.mean(gamma) > st.mean(pool))
    sig_loc = (not math.isnan(p_t) and p_t < 0.05) or (not math.isnan(p_u) and p_u < 0.05)
    # **预先写定的方差判据（Lead 2026-10-13）**：
    #   只有当 `Levene(Γ-guided vs 组内残差池) p < 0.05` 且 Γ-guided 的 sd 点估计更小时，
    #   才允许写"方差更小"；否则一律写"不可区分"，**不得提及方差**。
    var_smaller = ((not math.isnan(p_in)) and p_in < 0.05
                   and (not math.isnan(gamma_sd)) and gamma_sd < (within_sd_median
                                                                  if not math.isnan(within_sd_median)
                                                                  else float("inf")))
    # ---- 功效诊断（Lead 2026-10-13 提出）：同分配内 seed 极差 vs 方案间差异 ----
    #
    # 若"同分配内 seed 极差" ≥ "方案间均值差"，则任何方案间 p 值都不可靠
    # （实测 `random_01` 的 seed 极差 10,912.9 是 `exp` vs `uniform` 差异 4,172 的 2.6×）。
    within_ranges = {n: (max(v) - min(v)) for n in per_plan
                     if len(v := [r["delta_E"] for r in runs.values()
                                  if r.get("plan") == n]) > 1}
    max_within = max(within_ranges.values()) if within_ranges else float("nan")
    between_diff = abs(st.mean(gamma) - st.mean(pool))
    underpowered = (not math.isnan(max_within)) and max_within >= between_diff

    if gamma_worse and sig_loc and not underpowered:
        verdict = "GAMMA_NOT_BETTER_THAN_RANDOM"
    elif underpowered:
        verdict = "UNDERPOWERED_TO_DISTINGUISH"
    elif var_smaller:
        verdict = "INDISTINGUISHABLE_BUT_LOWER_VARIANCE"
    else:
        verdict = "INDISTINGUISHABLE"

    print(f"\n=== 检验 ===")
    print(f"  Welch t = {t:.3f}, p = {p_t:.4f}")
    print(f"  Mann-Whitney U = {u:.1f}, p = {p_u:.4f}")
    print(f"  Levene（Γ-guided vs 混合池）W = {w:.3f}, p = {p_w:.4f}")
    print(f"  Levene（Γ-guided vs **组内残差池**）W = {w_in:.3f}, p = {p_in:.4f}  ← 方差判据用这个")
    print(f"  Γ-guided 均值的经验分位 = {pct:.1f}%（随机池 {len(pool)} 个 run 中 "
          f"{below} 个更低）")
    print(f"\n=== 方差分解（Lead 口径）===")
    print(f"  池的**组间 sd**（{len(arm_means)} 个方案均值之间）= {between_sd:,.1f}")
    print(f"  池的**组内 sd 中位数**（各方案内 seed sd 的中位）= {within_sd_median:,.1f}")
    print(f"  混合池 sd（同时含组间+组内，**不应直接比**）= {st.stdev(pool):,.1f}")
    print(f"  Γ-guided 的 sd（单一方案组内，n={len(gamma)}）= {gamma_sd:,.1f}")
    print(f"  ⇒ 方差判据（Levene(组内残差) p<0.05 且 Γ-guided sd 更小）: "
          f"{'满足 → 可写「方差更小」' if var_smaller else '**不满足 → 一律写「不可区分」，不得提及方差**'}")
    print(f"\n=== 功效诊断 ===")
    print(f"  各随机方案内 seed 极差: "
          f"{ {n: round(r, 1) for n, r in within_ranges.items()} }")
    print(f"  最大同分配内极差 = {max_within:,.1f}｜方案间均值差 = {between_diff:,.1f}"
          f"｜比值 = {max_within / between_diff if between_diff else float('nan'):.2f}×")
    print(f"  ⇒ {'⚠️ 同分配内噪声 ≥ 方案间差异 → 功效不足' if underpowered else '功效诊断通过'}")
    print(f"\n=== 判定（规则写死在脚本内）: {verdict}"
          + ("  ｜ ⚠️ 数据不足，仅供参考（正式判定需随机池 ≥5 run）" if partial else "")
          + " ===")

    rec = {
        "script": "tools/_p458_random_pool_test.py",
        "gamma_plan": GAMMA_PLAN,
        "random_plans_used": rand_plans,
        "random_plans_excluded_as_duplicate_of_corner": dup,
        "gamma": {"n": len(gamma), "mean": st.mean(gamma),
                  "sd": st.stdev(gamma), "values": gamma},
        "random_pool": {"n": len(pool), "mean": st.mean(pool), "sd": st.stdev(pool),
                        "values": pool, "per_plan": per_plan},
        "tests": {"welch_t": t, "welch_p": p_t, "mannwhitney_u": u,
                  "mannwhitney_p": p_u,
                  "levene_mixed_pool_W": w, "levene_mixed_pool_p": p_w,
                  "levene_within_resid_W": w_in, "levene_within_resid_p": p_in,
                  "levene_note": "方差判据用 within_resid（Γ-guided vs 组内残差池）；"
                                 "mixed_pool 版本含组间差异，不应直接比"},
        "variance_decomposition": {
            "between_arm_sd": between_sd,
            "within_arm_sd_median": within_sd_median,
            "mixed_pool_sd": st.stdev(pool),
            "gamma_sd": gamma_sd,
            "note": "池 sd 同时含组间与组内；Γ-guided sd 是单一方案组内 sd —— 两者不是同一个量",
        },
        "variance_claim_allowed": bool(var_smaller),
        "variance_claim_rule":
            "只有当 Levene(Γ-guided vs 组内残差池) p<0.05 且 Γ-guided sd 点估计更小时，"
            "才允许写「方差更小」；否则写「不可区分」且不得提及方差",
        "gamma_mean_percentile_in_random_pool": pct,
        "gamma_worse_than_pool": bool(gamma_worse),
        "power_diagnosis": {
            "within_plan_seed_ranges": {k: v for k, v in within_ranges.items()},
            "max_within_plan_range": max_within,
            "between_plan_mean_diff": between_diff,
            "ratio": (max_within / between_diff) if between_diff else None,
            "underpowered": bool(underpowered),
            "rule": "同分配内 seed 极差 ≥ 方案间均值差 ⇒ 判为功效不足",
        },
        "verdict": verdict,
        "verdict_rules": {
            "GAMMA_NOT_BETTER_THAN_RANDOM":
                "Γ-guided 均值更高 且 位置检验 p<0.05 且 **功效诊断通过**",
            "UNDERPOWERED_TO_DISTINGUISH":
                "最大同分配内 seed 极差 ≥ 方案间均值差（噪声压过效应）",
            "INDISTINGUISHABLE_BUT_LOWER_VARIANCE":
                "功效通过 + 位置不可区分 + Levene p<0.05 且 Γ-guided 方差更小",
            "INDISTINGUISHABLE": "以上都不成立",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
