# -*- coding: utf-8 -*-
r"""核 task-9 的三条（AdaLoRA 未真训练 / +1296 参数量溯源 / 聚合修复）（2026-10-13）。

1. **AdaLoRA 几乎没训练**：loss 1.5595→1.5604（不降）、E 小幅震荡
   ⇒ **不能声称优劣**（学习程度与 GFAP 侧不可比）
2. **参数量 +1,296**：`lora_A 3,182,592 + lora_B 4,055,040 + lora_E 1,296 = 7,238,928`
   ⇒ **A+B 逐位 = 预算 7,237,632**；多出的是 **324 模块 × rank4 个 `lora_E`**
3. **聚合根因**：`_p440_aggregate.py` 原读 `<tag>/summary.json`（每次调用被重写、只含本次方案）
   ⇒ P1 补跑时**静默丢掉 4 个规则方案**；现改读逐 run 独立 JSON，**45 run 全部回来**

    python tools\_p466_verify_adalora.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_adalora_verified.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① AdaLoRA run 是否真训练（loss 是否下降）")
    print("=" * 100)
    fs = sorted(glob.glob(str(REPO / "outputs/analysis/p3_alloc_runs/*/adalora*.json")))
    if not fs:
        fs = sorted(glob.glob(str(REPO / "outputs/analysis/**/*adalora*.json"), recursive=True))
    print(f"  找到 {len(fs)} 个文件")
    for f in fs[:6]:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        print(f"  ── {os.path.basename(f)} ──")
        for k in ("plan", "seed", "family", "delta_E", "E_trajectory", "train_loss",
                  "loss_first", "loss_last", "n_trainable_params_measured",
                  "n_trainable_params_expected", "ok", "epochs", "batch", "lr"):
            if k in d:
                v = d[k]
                s = json.dumps(v, ensure_ascii=False) if not isinstance(v, (int, float, str)) else v
                print(f"     {k:<32} {str(s)[:130]}")
        # per-tensor 分解（若有）
        for k in d:
            if "lora" in k.lower() and isinstance(d[k], dict):
                print(f"     {k} = {json.dumps(d[k], ensure_ascii=False)[:200]}")
        print()

    print("=" * 100)
    print("② 对比：GFAP 侧 loss 是否下降（证明两侧学习程度不可比）")
    print("=" * 100)
    for plan in ("uniform", "exp_beta_paper_0.137"):
        g = sorted(glob.glob(str(REPO / f"outputs/analysis/p3_alloc_runs/main/{plan}__seed*.json")))
        for f in g[:1]:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            tl = d.get("train_loss")
            print(f"  {plan:<26} train_loss = {tl if not isinstance(tl, list) else [round(x,4) for x in tl]}")
    rep["adalora_files"] = len(fs)

    print()
    print("=" * 100)
    print("③ 参数量溯源核对（算术）")
    print("=" * 100)
    BUDGET = 7237632
    A, B, E = 3182592, 4055040, 1296
    print(f"  lora_A + lora_B      = {A:,} + {B:,} = {A+B:,}")
    print(f"  预算                 = {BUDGET:,}")
    print(f"  ⇒ A+B 逐位等于预算 ? {A+B == BUDGET}")
    print(f"  再 + lora_E({E:,})    = {A+B+E:,}  （实测 {7238928:,}）")
    print(f"  ⇒ 与 7,238,928 一致 ? {A+B+E == 7238928}")
    print(f"  偏差 % = {100*E/BUDGET:.4f}%")
    print(f"  324 模块 × rank 4 = {324*4} ⇒ lora_E 总数 {E} ? {324*4 == E}")
    rep["param_accounting"] = {"A": A, "B": B, "E": E, "budget": BUDGET,
                              "A_plus_B_equals_budget": A + B == BUDGET,
                              "total": A + B + E, "deviation_pct": round(100 * E / BUDGET, 4),
                              "n_modules_x_rank": 324 * 4}

    print()
    print("=" * 100)
    print("④ 聚合修复核对：45 个 run 是否全部回来")
    print("=" * 100)
    g = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs/analysis/p3_alloc_runs/*/*.json")):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        if isinstance(d.get("delta_E"), (int, float)):
            g[str(d.get("plan"))].append(d["delta_E"])
    print(f"  方案数 = {len(g)} ｜ run 总数 = {sum(len(v) for v in g.values())}")
    for k in sorted(g):
        print(f"     {k:<30} n={len(g[k])}")
    rep["plans_in_details"] = {k: len(v) for k, v in g.items()}

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
