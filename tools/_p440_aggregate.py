# -*- coding: utf-8 -*-
r"""task-9 步骤 5：汇总同预算训练结果 → 统计对比 → 归档（R2.2 / R3.21 的结果表）。

## 统计口径（诚实优先）

每个方案在多个 seed 上各跑一次，得到 `ΔE = E1 − E0`。汇总给出：

1. **逐方案**：mean ± **样本** sd（n−1）、median、**NaN/崩溃计数**（论文说 random 组
   会出现 NaN 塌缩，本表要能显示同类失败）；
2. **关键对比**（同预算）：
   - Γ-guided vs uniform：Welch t（不假设等方差）
   - Γ-guided vs random：**置换检验**（random 方案的 20 个不同分配 × seeds 构成零分布）
     —— 比 t 检验更适合"分配方案"这种离散选择
   - 反序（inverse）作为方向性 sanity check
3. **"名义最优"参照**：exact_opt / corner 的实测值，用于判断 Γ-guided 离理论最优多远。

**不做的**：不做多重比较的"挑最好的报"。所有方案全部列出，即使 Γ-guided 不占优。

## 用法

    python tools\_p440_aggregate.py --apply
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
OUT = REPO / "outputs" / "analysis" / "p3_alloc_results.json"


def welch_t(a, b):
    """Welch t 检验（不假设等方差）。返回 (t, df, 双尾 p 近似)。"""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan"), float("nan"), float("nan")
    ma, mb = st.mean(a), st.mean(b)
    va, vb = st.variance(a), st.variance(b)
    se2 = va / na + vb / nb
    if se2 <= 0:
        return float("nan"), float("nan"), float("nan")
    t = (ma - mb) / math.sqrt(se2)
    df = se2 ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    # 用 Student-t 双尾 p（scipy 可用则用；否则给 NaN 并标注）
    try:
        from scipy import stats
        p = float(2 * stats.t.sf(abs(t), df))
    except Exception:  # noqa: BLE001
        p = float("nan")
    return float(t), float(df), p


def described(vals):
    vals = [v for v in vals if v is not None and math.isfinite(v)]
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "mean": st.mean(vals),
            "sd": (st.stdev(vals) if len(vals) > 1 else 0.0),
            "median": st.median(vals), "min": min(vals), "max": max(vals)}


def main() -> int:
    if "--apply" not in sys.argv:
        print("=== 汇总（预演）===")
        print(f"  读 {RUNDIR}/*/summary.json")
        print("  --apply 实跑")
        return 0

    plans = json.loads(io.open(PLANS, encoding="utf-8").read())
    budget = plans["budget_params"]

    # 收集 run：**以逐 run 的独立 JSON 为准**，而不是 tag 目录下的 `summary.json`。
    #
    # 为什么改（2026-10-13 实测教训）：`_p434_alloc_train.py` 每次调用都会**重写**
    # `<tag>/summary.json`，只包含**本次调用**跑过/跳过的方案。P1 补跑时我只传了
    # random 方案 → `summary.json` 里**规则方案（uniform/exp/corner/inverse）全部消失**，
    # 于是聚合结果静默丢掉了对照臂（Lead 发现字段出处失效）。
    # 逐 run 文件 `<tag>/<plan>__seed<k>.json` 是**只增不改**的，故为稳定来源。
    runs: dict[str, dict] = {}
    tags = []
    run_files = 0
    if not RUNDIR.exists():
        print(f"[FATAL] 缺 {RUNDIR.relative_to(REPO)}：先跑 tools/_p434_alloc_train.py --apply")
        return 1
    for tagdir in sorted(p for p in RUNDIR.iterdir() if p.is_dir()):
        found_any = False
        for f in sorted(tagdir.glob("*.json")):
            if f.name == "summary.json":
                continue
            try:
                rec = json.loads(io.open(f, encoding="utf-8").read())
            except Exception as exc:  # noqa: BLE001
                print(f"  [warn] 读不动 {f.name}: {exc}")
                continue
            if not isinstance(rec, dict) or "plan" not in rec:
                continue          # 例如 adalora_probe.json 这类非 run 文件
            # 同名 run 以**后写的 tag 目录**为准（当前只有一个 main，逻辑上是恒等）
            runs[f"{tagdir.name}/{f.stem}"] = rec
            found_any = True
            run_files += 1
        if found_any:
            tags.append(tagdir.name)
    print(f"读到 {len(runs)} 个 run（逐 run 文件 {run_files} 个），来自 tag {tags}")

    # 逐方案聚合
    by_plan: dict[str, list[dict]] = {}
    for key, r in runs.items():
        by_plan.setdefault(r["plan"], []).append(r)

    print("\n=== 逐方案 ΔE（同预算 %s 参数）===" % f"{budget:,}")
    hdr = f"{'plan':<26}{'n_ok':>5}{'n_fail':>7}{'mean ΔE':>12}{'sd':>10}{'median':>12}"
    print(hdr)
    table = {}
    for name in sorted(by_plan):
        recs = by_plan[name]
        ok = [r for r in recs if r.get("ok") and r.get("delta_E") is not None]
        fails = [r for r in recs if not r.get("ok")]
        d = described([r["delta_E"] for r in ok])
        table[name] = {
            "family": recs[0].get("family"), "beta": recs[0].get("beta"),
            "ranks": recs[0].get("ranks"),
            "n_trainable_params_measured":
                sorted({r.get("n_trainable_params_measured") for r in ok if
                        r.get("n_trainable_params_measured")}),
            "delta_E": d,
            "n_failed": len(fails),
            "failures": [{"seed": r["seed"], "error": r.get("error")} for r in fails],
            "delta_E_per_sample_mean": described(
                [r.get("delta_E_per_sample_mean") for r in ok]),
            "loss_first": described([r.get("loss_first") for r in ok]),
            "loss_last": described([r.get("loss_last") for r in ok]),
            "peak_gpu_gib": described([r.get("peak_gpu_gib") for r in ok]),
        }
        m = d.get("mean") if d.get("n") else None
        s = d.get("sd") if d.get("n") else None
        md = d.get("median") if d.get("n") else None
        print(f"{name:<26}{d.get('n', 0):>5}{len(fails):>7}"
              f"{(f'{m:+.2f}' if m is not None else 'n/a'):>12}"
              f"{(f'{s:.2f}' if s is not None else 'n/a'):>10}"
              f"{(f'{md:+.2f}' if md is not None else 'n/a'):>12}")

    # 同预算校验：所有 run 的实测参数量必须唯一
    all_params = sorted({p for t in table.values()
                         for p in t["n_trainable_params_measured"]})
    print(f"\n=== 同预算校验 ===")
    print(f"  所有 run 实测可训参数量集合 = {all_params}")
    budget_ok = (len(all_params) == 1 and all_params[0] == budget)
    print(f"  {'OK' if budget_ok else 'FAIL'} 全部逐位等于预算 {budget:,}")

    # 关键对比
    def vals(name):
        return [r["delta_E"] for r in by_plan.get(name, [])
                if r.get("ok") and r.get("delta_E") is not None]

    comparisons = {}
    uni = vals("uniform")
    rand_all = [v for n in by_plan if n.startswith("random_") for v in vals(n)]
    for name in ("exp_beta_paper_0.137", "exp_beta_1e-4", "exp_beta_3e-4",
                 "exp_beta_1e9", "exp_ca_beta_paper_0.137",
                 "inverse_beta_paper_0.137", "exact_opt", "corner",
                 "exp_beta_0"):
        v = vals(name)
        if not v:
            continue
        t_u, df_u, p_u = welch_t(v, uni)
        comparisons[name] = {
            "n": len(v), "mean": st.mean(v),
            "vs_uniform": {"welch_t": t_u, "df": df_u, "p_two_sided": p_u,
                           "uniform_mean": st.mean(uni) if uni else None,
                           "uniform_n": len(uni)},
            "vs_random_pool": {"random_mean": st.mean(rand_all) if rand_all else None,
                               "random_n": len(rand_all),
                               "delta_mean": (st.mean(v) - st.mean(rand_all))
                               if rand_all else None},
        }
    # 置换检验：Γ-guided 的 rank 在"全部方案均值"里的位置
    if rand_all and vals("exp_beta_paper_0.137"):
        all_means = {n: st.mean(vals(n)) for n in by_plan if vals(n)}
        target = all_means["exp_beta_paper_0.137"]
        better = sum(1 for n, m in all_means.items() if m < target)
        comparisons["exp_beta_paper_0.137"]["rank_among_plans"] = {
            "n_plans_compared": len(all_means),
            "n_plans_with_lower_mean_delta_E": better,
            "fraction_better": better / len(all_means),
            "note": "ΔE 越小越好；此比例即'随机挑一个方案比 Γ-guided 更好'的经验概率",
        }

    rec = {
        "script": "tools/_p440_aggregate.py",
        "plans_source": "outputs/analysis/p3_alloc_plans.json",
        "runs_source": "outputs/analysis/p3_alloc_runs/*/summary.json",
        "tags": tags,
        "budget_params": budget,
        "same_budget_assert_passed": bool(budget_ok),
        "measured_n_trainable_params": all_params,
        "n_runs_total": len(runs),
        "per_plan": table,
        "comparisons": comparisons,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"\n已写 {OUT.relative_to(REPO)}")
    if not budget_ok:
        print("  [FATAL] 同预算校验未通过 —— 结果不可用于答复 R3.21")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
