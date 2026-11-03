# -*- coding: utf-8 -*-
r"""补充：τ 在**逐 run 内**的排序力与「能否识别坏检查点」（2026-12-12）。

## 为什么补

`_p236` 的结论是：τ 最大 ↔ 固定 ep1 ↔ oracle 三者**平均 top-1 完全相同（59.66）**，
因为三条轨迹的 τ 与 top-1 都从 ep1 起单调下降 → **所有准则都选 ep1**。

**但"选到同一个点"不等于"τ 无信息"**：还要看
① τ 与 top-1 在**逐 run 内**的相关（排序力）
② 若训练继续（把 ep1 排除），τ 能否指出后面哪个检查点更差
③ τ 与 val_loss 的**分歧**出现在哪里

    python tools\_p241_within_run_rank.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "outputs" / "a1_class_aligned" / "lr0.0"
OUT = REPO / "outputs" / "analysis" / "a1_within_run_rank.json"


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


def rank(v):
    s = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    for pos, i in enumerate(s):
        r[i] = pos + 1
    return r


def spearman(xs, ys):
    return pearson(rank(xs), rank(ys)) if len(xs) > 1 else float("nan")


def fisher(rs):
    zs = [math.atanh(max(-0.999, min(0.999, r))) for r in rs if not math.isnan(r)]
    return math.tanh(st.mean(zs)) if zs else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    runs = defaultdict(dict)
    for f in sorted(glob.glob(str(ROOT / "seed*" / "eval_epoch*.json"))):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        runs[Path(f).parent.name][d["eval_epoch"]] = d

    print("=" * 92)
    print("① 逐 run 内：τ vs top-1 vs val_loss 的相关（n=10 epoch）")
    print("=" * 92)
    print(f"  {'run':<10}{'ρ(τ,top1)':>12}{'r(τ,top1)':>12}{'ρ(vloss,top1)':>15}"
          f"{'ρ(τ,vloss)':>13}")
    res, rhos_t, rhos_v = {}, [], []
    for s in sorted(runs):
        v = runs[s]
        eps = sorted(v)
        tau = [v[e]["tau_final"] for e in eps]
        t1 = [v[e]["top1_50k"] for e in eps]
        vl = [v[e]["val_loss"] for e in eps]
        rt = spearman(tau, t1)
        rp = pearson(tau, t1)
        rv = spearman(vl, t1)
        rtv = spearman(tau, vl)
        rhos_t.append(rt)
        rhos_v.append(rv)
        res[s] = {"n": len(eps), "spearman_tau_top1": round(rt, 4),
                  "pearson_tau_top1": round(rp, 4),
                  "spearman_vloss_top1": round(rv, 4),
                  "spearman_tau_vloss": round(rtv, 4)}
        print(f"  {s:<10}{rt:>12.4f}{rp:>12.4f}{rv:>15.4f}{rtv:>13.4f}")
    print()
    print(f"  τ–top1 的 Fisher 平均 = **{fisher(rhos_t):+.4f}**")
    print(f"  val_loss–top1 的 Fisher 平均 = {fisher(rhos_v):+.4f}")

    print()
    print("=" * 92)
    print("② 排除 ep1 后（模拟「ep1 不可用/训练继续」），τ 还能排序吗")
    print("=" * 92)
    print(f"  {'run':<10}{'ρ(τ,top1) ep2-10':>20}{'ρ(vloss,top1) ep2-10':>22}")
    r2t, r2v = [], []
    for s in sorted(runs):
        v = runs[s]
        eps = [e for e in sorted(v) if e >= 2]
        tau = [v[e]["tau_final"] for e in eps]
        t1 = [v[e]["top1_50k"] for e in eps]
        vl = [v[e]["val_loss"] for e in eps]
        rt, rv = spearman(tau, t1), spearman(vl, t1)
        r2t.append(rt)
        r2v.append(rv)
        print(f"  {s:<10}{rt:>20.4f}{rv:>22.4f}")
    print()
    print(f"  Fisher 平均：τ = **{fisher(r2t):+.4f}** ｜ val_loss = {fisher(r2v):+.4f}")

    print()
    print("=" * 92)
    print("③ τ 与 val_loss 的分歧（选点不同处）")
    print("=" * 92)
    for s in sorted(runs):
        v = runs[s]
        eps = sorted(v)
        best_tau = max(eps, key=lambda e: v[e]["tau_final"])
        best_vl = min(eps, key=lambda e: v[e]["val_loss"])
        d_t1 = v[best_tau]["top1_50k"] - v[best_vl]["top1_50k"]
        print(f"  {s}: τ→ep{best_tau}({v[best_tau]['top1_50k']:.2f}) ｜ "
              f"vloss→ep{best_vl}({v[best_vl]['top1_50k']:.2f}) ｜ 差 {d_t1:+.2f} 点")

    print()
    print("=" * 92)
    print("④ 判定")
    print("=" * 92)
    ft = fisher(rhos_t)
    fv = fisher(rhos_v)
    print(f"  逐 run 内 τ–top1 相关：{ft:+.4f}（3/3 run 为正？"
          f"{'✅' if all(r > 0 for r in rhos_t) else '否'}）")
    print(f"  逐 run 内 val_loss–top1 相关：{fv:+.4f}")
    if ft > 0.5:
        print(f"  ✅ **τ 在逐 run 内能排序检查点**（Fisher {ft:+.3f}）")
    else:
        print(f"  🔴 τ 逐 run 内排序力不足（Fisher {ft:+.3f}）")
    if ft > fv:
        print(f"  ✅ **τ 排序力优于 val_loss**（{ft:+.3f} vs {fv:+.3f}）")
    else:
        print(f"  🔴 τ 排序力不优于 val_loss（{ft:+.3f} vs {fv:+.3f}）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": "outputs/a1_class_aligned/lr0.0/seed*/eval_epoch*.json",
             "per_run": res, "fisher_tau_top1": round(ft, 4),
             "fisher_vloss_top1": round(fv, 4),
             "excl_ep1": {"fisher_tau": round(fisher(r2t), 4),
                          "fisher_vloss": round(fisher(r2v), 4)}},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
