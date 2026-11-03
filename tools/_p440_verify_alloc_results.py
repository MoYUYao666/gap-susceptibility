# -*- coding: utf-8 -*-
r"""核 task-9 的关键数字（2026-10-12/13）。

## 待核（每条都会改稿）

1. **15 run 的实测参数量唯一值 = 7,237,632**（`same_budget_assert_passed`）
2. **Γ-guided（+2241）优于 uniform（+6413）**，Welch **p=0.024**（n=3）
3. ⚠️ **反序（+2225）与正序（+2241）几乎不可区分** → **方向性主张未获支持**
4. ⚠️ **同预算随机（+1103）均值最低** → **Γ-guided 未胜过随机**
5. ⚠️ **`corner`（+3607）劣于 `exp`** → **线性目标不是实测 ΔE 的好代理**
6. **Qwen2-VL-2B 的 Γ 符号混合**（vision/deep 负、shallow/mid 正）→ 稿件 Finding 4 称"uniformly negative"

    python tools\_p440_verify_alloc_results.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_alloc_verified.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 归档清单")
    print("=" * 100)
    for f in ("p3_alloc_budget_probe.json", "p3_alloc_gamma_qwen2vl2b.json",
              "p3_alloc_plans.json", "p3_alloc_results.json",
              "p3_alloc_adalora_config.json", "p3_alloc_gpu_calib.json"):
        p = REPO / "outputs" / "analysis" / f
        print(f"  {'✅' if p.exists() else '⚠️ '} {f}"
              + (f"  {os.path.getsize(p):,} B" if p.exists() else ""))

    print()
    print("=" * 100)
    print("② 预算断言 + 各方案 ΔE（逐 seed）")
    print("=" * 100)
    p = REPO / "outputs" / "analysis" / "p3_alloc_results.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        print(f"  顶层键：{sorted(d.keys())[:14]}")
        ntp = d.get("measured_n_trainable_params")
        print(f"  measured_n_trainable_params = {ntp}")
        print(f"  same_budget_assert_passed  = {d.get('same_budget_assert_passed')}")
        rep["measured_n_trainable_params"] = ntp
        rep["same_budget_assert_passed"] = d.get("same_budget_assert_passed")
        print()
        # 找逐方案结果
        for key in ("plans", "results", "by_plan", "summary", "per_plan"):
            if key in d:
                v = d[key]
                print(f"  ── {key} （{type(v).__name__}）──")
                if isinstance(v, dict):
                    for name, vv in v.items():
                        if isinstance(vv, dict):
                            des = vv.get("dE_values") or vv.get("dEs") or vv.get("delta_E")
                            print(f"     {name:<16} {json.dumps({k: x for k, x in vv.items() if k in ('ranks','rank_vector','dE_values','mean','sd','n_seeds')}, ensure_ascii=False)[:200]}")
                        else:
                            print(f"     {name:<16} {vv}")
                break

    print()
    print("=" * 100)
    print("③ Qwen2-VL-2B 逐块 Γ（R3.12）")
    print("=" * 100)
    p = REPO / "outputs" / "analysis" / "p3_alloc_gamma_qwen2vl2b.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        g = d.get("gamma_final") or d.get("gamma") or {}
        print(f"  gamma_final = {json.dumps(g, ensure_ascii=False)[:600]}")
        for k, v in g.items():
            if isinstance(v, dict):
                print(f"     {k:<16} {json.dumps(v, ensure_ascii=False)[:200]}")
            else:
                print(f"     {k:<16} {v}")
        rep["gamma_qwen2vl2b"] = g

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
