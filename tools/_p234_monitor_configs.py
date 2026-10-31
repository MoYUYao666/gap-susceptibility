# -*- coding: utf-8 -*-
r"""核 `a1_class_aligned` 的哪些配置可复用于监控决策实验（2026-10-12）。

## 要做什么

补"监控器决策"的真实验：需要**逐 epoch 的 (val_loss, τ, 下游 top-1) 三元组**，
才能比较"按 τ 停 vs 按 val_loss 停 vs 按 top-1 停"。

`tools/train_class_aligned.py` 的 `--eval-only --epoch N` 正好产出该三元组，
且**逐 epoch 权重已存盘**（`epoch{N}.pt`）。

**本脚本**：列出可用的 (配置, seed) 组合，并确认 epoch 权重齐全。

    python tools\_p234_monitor_configs.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "outputs" / "a1_class_aligned"
OUT = REPO / "outputs" / "analysis" / "a1_monitor_configs.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 90)
    print("① a1_class_aligned 下所有 (配置, seed)：epoch 权重与已有评测")
    print("=" * 90)
    rows = []
    for cfgs in sorted(glob.glob(str(ROOT / "*"))):
        cfg = Path(cfgs).name
        if not Path(cfgs).is_dir() or cfg.startswith("_"):
            continue
        for seeds in sorted(glob.glob(str(Path(cfgs) / "seed*"))):
            sd = Path(seeds)
            cks = sorted(sd.glob("epoch*.pt"),
                         key=lambda p: int("".join(c for c in p.stem if c.isdigit())))
            evs = sorted(sd.glob("eval_epoch*.json"))
            res = sd / "results.json"
            lam = None
            if res.exists():
                lam = json.loads(io.open(res, encoding="utf-8",
                                         errors="replace").read()).get("lambda_reg")
            rows.append({"cfg": cfg, "seed": sd.name, "n_ckpt": len(cks),
                         "ckpt_epochs": [int("".join(c for c in p.stem if c.isdigit()))
                                         for p in cks],
                         "evals": [p.stem.replace("eval_epoch", "") for p in evs],
                         "lambda_reg": lam})
            print(f"  {cfg:<20} {sd.name:<10} λ={str(lam):<6} "
                  f"权重 {len(cks)} 个 {rows[-1]['ckpt_epochs']} ｜ 已评测 {len(evs)} 个 "
                  f"{rows[-1]['evals']}")

    print()
    print("=" * 90)
    print("② 可做「逐 epoch 决策实验」的配置（需 10 个权重）")
    print("=" * 90)
    usable = [r for r in rows if r["n_ckpt"] >= 10 and r["lambda_reg"] == 0.0]
    for r in usable:
        need = [e for e in range(1, 11) if str(e) not in r["evals"]]
        print(f"  ✅ {r['cfg']}/{r['seed']}：权重齐全；**待评测 epoch {need}**")
    if not usable:
        print("  🔴 没有 λ=0 且权重齐全的配置")
    else:
        total = sum(len([e for e in range(1, 11) if str(e) not in r["evals"]])
                    for r in usable)
        print(f"\n  → 共 {len(usable)} 个 run，需补评测 {total} 个 epoch")
        print(f"  → 每个 epoch 评测含 50k top-1 + val_loss + τ，预计 6–9 分钟")
        print(f"  → **总计约 {total * 7.5 / 60:.1f} 小时**（可后台串行）")

    print()
    print("=" * 90)
    print("③ 已有 eval_epoch 的三元组（可直接用，n=5 个 epoch）")
    print("=" * 90)
    for f in sorted(glob.glob(str(ROOT / "**" / "eval_epoch*.json"), recursive=True))[:8]:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        print(f"  {Path(f).parent.parent.name}/{Path(f).parent.name}/"
              f"{Path(f).stem:<14} τ={d.get('tau_final')} top1_50k={d.get('top1_50k')} "
              f"val_loss={round(d.get('val_loss'), 4) if d.get('val_loss') else None}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": rows, "usable_lambda0": usable}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
