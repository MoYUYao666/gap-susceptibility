# -*- coding: utf-8 -*-
r"""核 p3-allocation 的三条发现（2026-10-12）。

1. **记账口径不一致**：论文 (A3) 是 `Σ rank_k = C`（rank 记账），但审稿人问的是**参数量**记账
   `Σ rank_k·cost_k`；LoRA 每 rank 成本块间差 **2.65×**（vision 655,360 vs shallow 247,296）
   ⇒ "rank 均匀" ≠ "参数均匀"；均匀 r=4 的逐块参数量 **最大/最小 = 2.65×**。
2. **Eq. 5 的记账口径未说明**：`rank*_k ∝ exp(-β|Γ_k|)` 是 rank 归一下的 KKT 解；
   参数预算下会多出 `/cost_k` 因子。
3. **β=0.137 的出处**是 `outputs/analysis/ode_ledger.json::runs[90].beta`（**ODE 拟合的 β**），
   而 `theory.tex` **自己**说这个 β 与 Eq. 5 的 β 是**不同量** ⇒ "CLIP-derived" 说法站不住。

    python tools\_p419_verify_p3_alloc_findings.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_alloc_findings_verify.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 引用 178 与每 rank 成本")
    print("=" * 100)
    for f in ("outputs/analysis/p3_alloc_budget_probe.json",
              "outputs/analysis/p3_alloc_plans.json"):
        p = REPO / f
        if not p.exists():
            print(f"  ⚠️ 缺 {f}")
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        print(f"  ── {f} ──")
        s = json.dumps(d, ensure_ascii=False, indent=1)
        print(s[:1800])
        print()
        rep[f] = True

    print("=" * 100)
    print("② 稿件里是否有 'equal parameter budget'（R3.21 的术语要害）")
    print("=" * 100)
    for f in glob.glob(str(REPO / "paper3" / "paper_ieee" / "sections" / "*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"equal\s+(parameter|rank)\s+budget|parameter budget|rank budget",
                             t, re.I):
            ln = t[:m.start()].count("\n") + 1
            seg = " ".join(t[max(0, m.start() - 220):m.start() + 260].split())
            print(f"  [{Path(f).name}:{ln}] …{seg[:400]}…")
            print()

    print("=" * 100)
    print("③ (A3) 的记账口径定义")
    print("=" * 100)
    for f in glob.glob(str(REPO / "paper3" / "paper_ieee" / "sections" / "*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"\(A3\)|AX3", t):
            ln = t[:m.start()].count("\n") + 1
            seg = " ".join(t[max(0, m.start() - 120):m.start() + 300].split())
            print(f"  [{Path(f).name}:{ln}] …{seg[:380]}…")
    print()

    print("=" * 100)
    print("④ β=0.137 的出处核对")
    print("=" * 100)
    led = REPO / "outputs" / "analysis" / "ode_ledger.json"
    if led.exists():
        d = json.loads(io.open(led, encoding="utf-8", errors="replace").read())
        runs = d.get("runs", [])
        hit = [(i, r) for i, r in enumerate(runs) if abs(r.get("beta", 0) - 0.1371162965748463) < 1e-9]
        print(f"  runs 总数 {len(runs)}；命中 beta=0.1371162965748463 的 run：{len(hit)}")
        for i, r in hit[:3]:
            print(f"     runs[{i}]: {json.dumps({k: r[k] for k in list(r)[:8]}, ensure_ascii=False)[:220]}")
        betas = [r["beta"] for r in runs if isinstance(r.get("beta"), (int, float))]
        if betas:
            import statistics
            print(f"  全部 beta：n={len(betas)} 中位数={statistics.median(betas):.6f}")
    else:
        print("  ⚠️ 无 ode_ledger.json")

    print()
    print("=" * 100)
    print("⑤ 稿件里 'CLIP-derived' 与 β 的表述")
    print("=" * 100)
    for f in glob.glob(str(REPO / "paper3" / "paper_ieee" / "sections" / "*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"CLIP-derived|0\.137", t):
            ln = t[:m.start()].count("\n") + 1
            seg = " ".join(t[max(0, m.start() - 200):m.start() + 260].split())
            print(f"  [{Path(f).name}:{ln}] …{seg[:380]}…")
            print()

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
