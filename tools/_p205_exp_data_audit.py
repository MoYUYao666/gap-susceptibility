# -*- coding: utf-8 -*-
r"""确认"补两个实验"所需数据是否在手（2026-10-12）。

## 要补的两个实验（操作者选 C）

| # | 实验 | 需要的数据 |
|---|---|---|
| **E-A** | **留出检查点检验 + rival baseline**（解 FATAL 2） | 检查点级 (τ, top-1, **留出基准**, **\|λ\|/\|δ\| 基线**) |
| **E-B** | **监控决策闭环**（τ 早停 vs val-loss 早停） | **逐 epoch 的 (τ, 下游 top-1)** |

**本脚本**：查这两类数据在归档里是否存在，**若已在手则不需要新训练**。

    python tools\_p205_exp_data_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "a1_exp_data_audit.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 88)
    print("① 检查点级数据：找含 tau + 多个基准 top-1 的记录")
    print("=" * 88)
    for f in ("outputs/a1_h_offset.json", "outputs/a1_h_seed_summary.json",
              "outputs/a1_rr_summary.json", "outputs/a1_rr_e4_eval_archived.json",
              "outputs/a1_h_seeds_dtd_seed43.json", "outputs/a1_h_seeds_coco_seed43.json"):
        p = REPO / f
        if not p.exists():
            print(f"  ❌ {f}")
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        keys = list(d.keys())[:14] if isinstance(d, dict) else f"list[{len(d)}]"
        print(f"  ✅ {f}")
        print(f"       顶层: {str(keys)[:140]}")

    print()
    print("=" * 88)
    print("② 逐 epoch 数据：找 (epoch, tau, 下游 top-1)")
    print("=" * 88)
    fs = sorted(glob.glob(str(REPO / "outputs" / "**" / "eval_epoch*.json"),
                          recursive=True))
    print(f"  eval_epoch*.json: {len(fs)} 个")
    for f in fs[:6]:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        print(f"    {Path(f).parent.parent.name}/{Path(f).parent.name}/{Path(f).name}")
        print(f"      {json.dumps({k: v for k, v in d.items() if 'history' not in k}, ensure_ascii=False)[:220]}")
    if fs:
        d = json.loads(io.open(fs[0], encoding="utf-8", errors="replace").read())
        print(f"\n  单文件全部键: {list(d.keys())}")

    print()
    print("=" * 88)
    print("③ τ 轨迹（a1_tau_trajectory.json）能否支撑早停演示")
    print("=" * 88)
    p = REPO / "outputs" / "a1_tau_trajectory.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        print(f"  frozen: {d.get('frozen')}")
        for arm in ("both", "text_only"):
            rows = d.get(arm, [])
            print(f"  {arm}: {len(rows)} epoch ｜ 键 = {list(rows[0].keys()) if rows else '—'}")
        print("  → 含 (epoch, top1, CG, tau)：**可支撑早停决策演示**，但 top1 是 ImageNet 5k/50k，")
        print("     无 val_loss；val_loss 见 outputs/a1_class_aligned/lr0.0/seed42/eval_epoch*.json")

    print()
    print("=" * 88)
    print("④ 检查点权重是否还在（若要补测留出基准）")
    print("=" * 88)
    ck = sorted(glob.glob(str(REPO / "outputs" / "**" / "*.pt"), recursive=True))
    print(f"  找到 {len(ck)} 个 .pt")
    for f in ck[:10]:
        print(f"    {Path(f).relative_to(REPO)}")
    if len(ck) > 10:
        print(f"    …（另 {len(ck) - 10} 个）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"eval_epoch_files": len(fs), "checkpoint_pt": len(ck)},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
