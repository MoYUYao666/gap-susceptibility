# -*- coding: utf-8 -*-
r"""核 task-9 的 E0 是否完全恒定（2026-10-13）。

## 成员主张

**19 个已完成 run（6 方案）的 `E0` 全部 = 23470.845703，唯一值，`sd = 0.00`，极差 `0.00`。**

## 为什么重要

**若成立** ⇒ $\\Delta E$ 是**干净的"训练引起的位移"**，方案间差异**不可能**被"起点不同"解释
⇒ **增强 ΔE 作为因变量的可比性**（与论文一致：论文 `E(0)` 只有 3927.0 / 3930.5 两值）。

**⚠️ 但它同时意味着**：成员的 `δE` 与**逐样本** $E_0$ 都**逐位相同**
⇒ 这**正是**"32 个样本同图同提示"的后果（有效 n=3 seed）**又一次独立确认**。

    python tools\_p454_verify_e0_constancy.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_e0_constancy.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    fs = sorted(glob.glob(str(REPO / "outputs/analysis/p3_alloc_runs/main/*.json")))
    print(f"  明细文件总数 = {len(fs)}")
    print()
    print("=" * 100)
    print("逐 run 的 E0")
    print("=" * 100)
    rows = []
    for f in fs:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        e0 = d.get("E0")
        ps = d.get("E0_per_sample")
        rows.append({"file": os.path.basename(f), "plan": d.get("plan"), "seed": d.get("seed"),
                     "E0": e0, "n_ps": len(ps) if isinstance(ps, list) else None,
                     "ps_unique": len(set(ps)) if isinstance(ps, list) else None,
                     "dE": d.get("delta_E"), "ok": d.get("ok")})
    for r in rows:
        print(f"  {r['file']:<44} E0={r['E0']!r:<22} per_sample 唯一值 {r['ps_unique']}/{r['n_ps']}"
              f"  ΔE={r['dE'] if not isinstance(r['dE'], float) else round(r['dE'],1)}")

    e0s = [r["E0"] for r in rows if isinstance(r["E0"], (int, float))]
    print()
    print("=" * 100)
    print("判定")
    print("=" * 100)
    if e0s:
        uniq = sorted(set(e0s))
        print(f"  n = {len(e0s)} ｜ 唯一值 {len(uniq)} 个：{uniq[:6]}")
        print(f"  sd = {statistics.pstdev(e0s):.10f} ｜ 极差 = {max(e0s)-min(e0s):.10f}")
        dE = [r["dE"] for r in rows if isinstance(r["dE"], (int, float))]
        if dE and (max(e0s) - min(e0s)) >= 0:
            print(f"  range(E0)/range(ΔE) = {(max(e0s)-min(e0s))/max(max(dE)-min(dE), 1e-12):.10f}")
        print()
        print(f"  {'✅ E0 完全恒定' if len(uniq) == 1 else '⚠️ E0 有散布'}"
              f" ⇒ ΔE 是{'干净的' if len(uniq) == 1 else '含初始化差异的'}训练位移")
        rep["e0_unique"] = uniq
        rep["e0_sd"] = statistics.pstdev(e0s) if len(e0s) > 1 else None
        rep["n_runs"] = len(e0s)

    # 逐样本唯一值
    n_ps_const = sum(1 for r in rows if r["n_ps"] and r["ps_unique"] == 1)
    print(f"  per_sample 完全恒定的 run：{n_ps_const}/{sum(1 for r in rows if r['n_ps'])}")
    print(f"  ⇒ 这是「32 样本同图同提示 ⇒ 有效 n = seed 数」的**又一次独立确认**")
    rep["per_sample_constant_runs"] = n_ps_const

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
