# -*- coding: utf-8 -*-
r"""完整核 `plans` 字段里所有方案的重复（含 random_00..08+）（2026-10-13）。

## 已确认

`random_04` = `{vision:4, llm_mid:3, llm_deep:8, llm_shallow:1}` = `corner` = `exact_opt`
（三者 `linear_objective` 都是 **24,184.58060951729**）⇒ **同一分配，不可并列为独立方案**。

**我要把全部方案都过一遍**：若还有别的重复，"同预算随机"的有效样本数比看上去少。

    python tools\_p445_check_all_plan_dups.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_all_plan_dups.json"


def key(ranks):
    return (ranks.get("vision"), ranks.get("llm_shallow"), ranks.get("llm_mid"),
            ranks.get("llm_deep"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(REPO / "outputs/analysis/p3_alloc_plans.json",
                           encoding="utf-8", errors="replace").read())
    plans = d.get("plans", {})

    print("=" * 100)
    print(f"全部方案：{len(plans)} 个")
    print("=" * 100)
    byfam = defaultdict(list)
    bykey = defaultdict(list)
    for name, v in plans.items():
        rk = v.get("ranks") or {}
        if not rk:
            continue
        byfam[v.get("family")].append(name)
        bykey[key(rk)].append(name)

    for fam, names in sorted(byfam.items()):
        print(f"  {fam:<34} {len(names):>3} 个：{sorted(names)[:9]}{' …' if len(names) > 9 else ''}")

    print()
    print("=" * 100)
    print("按 rank 向量分组 —— 找重复分配")
    print("=" * 100)
    dups = {k: v for k, v in bykey.items() if len(v) > 1}
    print(f"  不同 rank 向量 {len(bykey)} 个 ｜ **重复的 {len(dups)} 组**")
    for k, v in sorted(dups.items()):
        fams = {plans[n].get("family") for n in v}
        obj = {plans[n].get("linear_objective") for n in v}
        print(f"     {k}")
        print(f"        方案：{sorted(v)}")
        print(f"        family：{fams}")
        print(f"        linear_objective：{obj}")

    print()
    print("=" * 100)
    print("**独立的同预算随机方案**（`family == random_same_budget`）")
    print("=" * 100)
    rnd = [n for n in plans if plans[n].get("family") == "random_same_budget"]
    print(f"  名义上 {len(rnd)} 个：{sorted(rnd)}")
    # 去掉与 non-random 方案重复的
    nonrandom_keys = {key(plans[n]["ranks"]) for n in plans
                      if plans[n].get("family") != "random_same_budget" and plans[n].get("ranks")}
    distinct = {}
    dup_with_other = []
    for n in sorted(rnd):
        k = key(plans[n]["ranks"])
        if k in distinct:
            dup_with_other.append((n, "与另一个 random 重复", distinct[k]))
        elif k in nonrandom_keys:
            dup_with_other.append((n, "与 non-random 方案重复",
                                   [m for m in plans if plans[m].get("ranks")
                                    and key(plans[m]["ranks"]) == k and
                                    plans[m].get("family") != "random_same_budget"]))
        else:
            distinct[n] = k
    print(f"  **可作独立随机样本 {len(distinct)} 个**：")
    for n, k in distinct.items():
        print(f"     {n:<12} {k}")
    if dup_with_other:
        print(f"  ⚠️ 应排除 {len(dup_with_other)} 个（与其它方案同一分配）：")
        for n, why, whom in dup_with_other:
            print(f"     {n:<12} {why} → {whom}")

    res = {"families": {k: sorted(v) for k, v in byfam.items()},
           "duplicate_groups": {str(k): sorted(v) for k, v in dups.items()},
           "independent_random_plans": sorted(distinct),
           "excluded_random_plans": [list(x) for x in dup_with_other]}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
