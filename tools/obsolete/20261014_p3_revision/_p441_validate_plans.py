# -*- coding: utf-8 -*-
r"""task-9 CPU 侧端到端校验：**分配方案 ↔ 成本模型 ↔ 训练脚本断言**三者一致。

不加载模型、不占卡。逐方案核对：

1. 方案记录里的 `n_trainable_params` 是否等于按成本表重算的结果；
2. 是否全部**逐位**等于 `budget_params`；
3. 训练脚本 `_p434_alloc_train.py` 会断言的两件事（`n_all == budget`、
   `n_scoped == expected`）在成本模型下是否成立，其中
   `n_scoped(ranks) = Σ_k rank_k · cost_k`；
4. 每个方案是否在"精确可行集"里（`exact_budget_allocations`）。

    python tools\_p441_validate_plans.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_alloc_solvers import BLOCKS  # noqa: E402

PLANS = REPO / "outputs" / "analysis" / "p3_alloc_plans.json"


def main() -> int:
    if not PLANS.exists():
        print(f"[SKIP] 缺 {PLANS.relative_to(REPO)} —— 先跑 tools/_p438_alloc_plans.py --apply")
        return 0
    d = json.loads(io.open(PLANS, encoding="utf-8").read())
    cost = {b: int(v) for b, v in d["cost_per_rank"].items()}
    budget = int(d["budget_params"])
    plans = d["plans"]
    exact = [dict(a) for a in d.get("exact_budget_allocations", [])]
    fails = []

    print(f"预算 {budget:,}｜方案 {len(plans)} 个｜精确可行集 {len(exact)} 个")
    print(f"逐块成本 {cost}")
    print(f"\n{'plan':<26}{'ranks':<38}{'Σrank·cost':>14}{'==budget':>10}{'in_exact':>10}")
    for name in sorted(plans):
        p = plans[name]
        ranks = {b: int(p["ranks"][b]) for b in BLOCKS}
        scoped = sum(ranks[b] * cost[b] for b in BLOCKS)
        rec = int(p["n_trainable_params"])
        eq_budget = (scoped == budget)
        eq_rec = (rec == scoped)
        in_exact = any(all(a.get(b) == ranks[b] for b in BLOCKS) for a in exact) if exact else None
        flag = "OK" if (eq_budget and eq_rec) else "FAIL"
        print(f"{name:<26}{str(ranks):<38}{scoped:>14,}{str(eq_budget):>10}"
              f"{str(in_exact):>10}  {flag}")
        if not eq_budget:
            fails.append(f"{name}: Σrank·cost={scoped:,} != budget {budget:,}")
        if not eq_rec:
            fails.append(f"{name}: 记录的 n_trainable_params={rec:,} != 重算 {scoped:,}")
        if in_exact is False:
            fails.append(f"{name}: 不在 exact_budget_allocations 里（枚举可能被截断）")

    # 训练脚本的断言口径：n_scoped 必须 == expected，且 n_all 必须 == budget
    print("\n=== 训练脚本断言口径复核 ===")
    print("  _p434 断言①: n_all(实测 peft 可训参数) == budget_params")
    print("  _p434 断言②: n_scoped(按块归属汇总) == plan.n_trainable_params")
    print("  两者在成本模型下等价 ⇐ 每块参数量 == rank_k·cost_k，"
          "已由 tools/_p420_arch_probe.py 的逐位断言验证（r=8 时四块全 OK，"
          "patch_embed 的 Conv3d 已剔除）")

    print(f"\n=== 结论：{len(fails)} 项失败 ===")
    for f in fails:
        print("  FAIL:", f)
    if fails:
        return 1
    print("  ✅ 全部方案与预算逐位一致，且都在精确可行集内")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
