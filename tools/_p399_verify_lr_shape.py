# -*- coding: utf-8 -*-
r"""核 task-7 的关键主张：1e-4 未饱和、3e-4 塌缩退化（2026-10-12）。

## 队友主张（会改我稿中表述）

1. **1e-4 不饱和**：三 seed = +0.7969 / +0.2600 / +0.2679 → sd **0.31**（只有 seed42 在 ≈+0.80）
2. **3e-4 不可解释**：seed42 = +0.8001，seed123 = **−0.8153**，且后者是**退化塌缩**
   （CG 0.0004 / DG 0.0008、train loss 全程 4.1600 = ln 64 均匀解、zero-shot 0.08%、R@1 0.0010）
3. **C 项 seed 特异**：1e-4 的 seed123/999 **复现归档**，只有 seed42 分叉

    python tools\_p399_verify_lr_shape.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_ext.json"
OUT = REPO / "outputs" / "analysis" / "lr_shape_verify.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(P, encoding="utf-8", errors="replace").read())
    runs = d.get("runs", [])
    print("=" * 96)
    print("① 单条 run 的键（找指标字段名）")
    print("=" * 96)
    if runs:
        print("  " + str(sorted(runs[0].keys())))
    g = defaultdict(list)
    for r in runs:
        g[str(r.get("lr"))].append(r)

    print()
    print("=" * 96)
    print("② 逐 lr × seed 的 ΔCG / zero-shot / 末态证据")
    print("=" * 96)
    rep = {}
    for lr in sorted(g, key=lambda x: float(x)):
        print(f"\n  lr = {lr}")
        vals = []
        for r in g[lr]:
            # 指标可能在多个位置，逐一试
            dc = r.get("dCG") or r.get("delta_CG")
            zs = r.get("zero_shot_top1_pct")
            for src in (r.get("final"), r.get("metrics"), r.get("eval")):
                if isinstance(src, dict):
                    dc = dc if dc is not None else src.get("dCG") or src.get("delta_CG")
                    zs = zs if zs is not None else src.get("zero_shot_top1_pct")
            trl = r.get("final_train_loss")
            r1 = r.get("R@1_mean") or r.get("R@1")
            if dc is not None:
                vals.append(float(dc))
            print(f"     seed={str(r.get('seed')):<5} ΔCG={dc if dc is None else round(float(dc),4):<10} "
                  f"zero-shot={zs if zs is None else round(float(zs),2):<8} "
                  f"R@1={r1 if r1 is None else round(float(r1),4):<8} "
                  f"train_loss={trl if trl is None else round(float(trl),4)}")
            if r.get("error"):
                print(f"        ⚠️ error: {str(r['error'])[:90]}")
        if vals:
            m = statistics.mean(vals)
            sd = statistics.pstdev(vals) if len(vals) > 1 else None
            print(f"     → ΔCG 均值 {m:+.4f} ｜ sd {sd if sd is None else round(sd,4)} ｜ n={len(vals)}")
            rep[lr] = {"n": len(vals), "mean": round(m, 6),
                       "sd": None if sd is None else round(sd, 6), "values": [round(v, 4) for v in vals]}

    print()
    print("=" * 96)
    print("③ ln(64) = 4.1589 —— 核 3e-4 seed123 的 train loss 是否卡在该值")
    print("=" * 96)
    print(f"  ln(64) = {math.log(64):.4f}")
    for lr in ("0.0003", "0.0001"):
        for r in g.get(lr, []):
            h = r.get("history") or []
            losses = []
            if isinstance(h, list):
                for e in h:
                    if isinstance(e, dict):
                        for k in ("train_loss", "loss"):
                            if k in e:
                                losses.append(e[k])
                                break
            print(f"  lr={lr} seed={r.get('seed')}: train_loss 序列 = "
                  f"{[round(x,4) for x in losses[:12]] if losses else '（无 history）'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
