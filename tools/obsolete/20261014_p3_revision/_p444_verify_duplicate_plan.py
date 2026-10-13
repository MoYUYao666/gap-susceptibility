# -*- coding: utf-8 -*-
r"""核 `random_04` 与 `corner` 是否同一 rank 向量（2026-10-13）。

## 成员主张

`random_04` 的 rank 向量 `{4,1,3,8}` 与 `corner` **完全相同**（obj 都是 24,185），
因为它在 15 个精确可行解里恰好抽到角点 ⇒ **报"随机分配"分布时不应把两者并列为独立方案**。

## 为什么重要

若属实，则"同预算随机"的可用样本**比看上去少一个**；且若把重复的当独立样本，
会**虚增随机组的 n**、并**重复计入一个极值**（角点的 +3607）。

    python tools\_p444_verify_duplicate_plan.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_plan_duplicate_check.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 全部方案的 rank 向量与 obj（找重复）")
    print("=" * 100)
    plans = json.loads(io.open(REPO / "outputs/analysis/p3_alloc_plans.json",
                               encoding="utf-8", errors="replace").read())
    print(f"  顶层键：{sorted(plans.keys())[:12]}")
    # 找方案列表
    lst = None
    for k in ("plans", "allocations", "exact_budget_allocations", "all_plans"):
        if k in plans and isinstance(plans[k], list):
            lst = plans[k]
            print(f"  方案列表字段：{k}（{len(lst)} 项）")
            break
    if lst is None:
        for k, v in plans.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                lst = v
                print(f"  方案列表字段（推断）：{k}（{len(v)} 项）")
                break

    if lst:
        print(f"  首项键：{sorted(lst[0].keys())}")
        rows = []
        for x in lst:
            name = x.get("name") or x.get("plan") or x.get("id")
            ranks = x.get("ranks") or x.get("rank_vector") or x.get("rank")
            obj = x.get("obj") or x.get("objective") or x.get("S")
            rows.append((name, json.dumps(ranks, sort_keys=True) if ranks else None, obj))
        print()
        seen = {}
        for name, rk, obj in rows:
            if rk is None:
                continue
            seen.setdefault(rk, []).append((name, obj))
        dups = {k: v for k, v in seen.items() if len(v) > 1}
        print(f"  不同 rank 向量 {len(seen)} 个 ｜ **有重复的向量 {len(dups)} 个**")
        for rk, v in dups.items():
            print(f"     {rk}  ← {v}")
        rep["duplicate_vectors"] = {k: [list(x) for x in v] for k, v in dups.items()}
        if not dups:
            print("     （无重复）")

    print()
    print("=" * 100)
    print("② 专项核对 random_04 vs corner")
    print("=" * 100)
    rs = json.loads(io.open(REPO / "outputs/analysis/p3_alloc_results.json",
                            encoding="utf-8", errors="replace").read())
    pp = rs.get("per_plan", {})
    for name in ("corner", "random_00", "uniform",
                 "exp_beta_paper_0.137", "inverse_beta_paper_0.137"):
        if name in pp:
            v = pp[name]
            print(f"  {name:<24} ranks={json.dumps(v.get('ranks'), ensure_ascii=False)}")
    # random_04 是否在 results 里
    r4 = {k: v for k, v in pp.items() if "random" in k}
    print(f"  results 里的 random* 方案：{sorted(r4.keys())}")
    rep["random_plans_in_results"] = sorted(r4.keys())

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
