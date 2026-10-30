# -*- coding: utf-8 -*-
r"""方案② 分析：组内 n=30 重检 τ 的排序力（决定标题怎么写）（2026-10-12）。

## 数据

`outputs/a1_epoch_sweep.json`（`tools/_p218`，100 个检查点，0 失败）

| 数据集 | 检查点 | n |
|---|---|---|
| coco | seed42/43/44 × epoch1–10 | 30 |
| dtd | 同上 | 30 |
| food101 | 同上 | 30 |
| flickr30k_ref | seed42 × epoch1–10 | 10 |

**这些是**真正的组内变异**（同一数据集、同一配置、不同训练进度/种子），
而非之前只有 3 个 seed（n=3 不可靠）。**

## 判据（决定标题）

| 结果 | 标题 |
|---|---|
| 组内 τ 显著为正（均值 > +0.3 且多数数据集为正） | 可保留"early-warning signal" |
| 组内 τ ≈ 0 或为负 | **只承诺"边界刻画"**，不得称监控器 |

    python tools\_p219_analyze_epoch_sweep.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "a1_epoch_sweep.json"
SRC_OLD = REPO / "outputs" / "a1_h_offset.json"
OUT = REPO / "outputs" / "analysis" / "a1_epoch_sweep_analysis.json"


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

    sw = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())
    rows = [r for r in sw["checkpoints"] if "error" not in r
            and isinstance(r.get("tau5"), (int, float))
            and isinstance(r.get("top1_5k"), (int, float))]
    print("=" * 92)
    print(f"① 数据：{len(rows)} 个检查点（来源 {SRC.name}，{sw['meta']['script']}）")
    print("=" * 92)
    by = {}
    for r in rows:
        by.setdefault(r["dataset"], []).append(r)
    for ds in sorted(by):
        v = by[ds]
        taus = [r["tau5"] for r in v]
        t1s = [r["top1_5k"] for r in v]
        print(f"  {ds:<16} n={len(v):<3} τ∈[{min(taus):.4f},{max(taus):.4f}] 跨度 {max(taus)-min(taus):.4f}  "
              f"top1∈[{min(t1s):.2f},{max(t1s):.2f}] 跨度 {max(t1s)-min(t1s):.2f}")

    # ② 组内相关
    print()
    print("=" * 92)
    print("② **组内** Spearman(τ, top1) —— 现在 n=30（之前 n=3）")
    print("=" * 92)
    within = {}
    for ds in sorted(by):
        v = by[ds]
        xs = [r["tau5"] for r in v]
        ys = [r["top1_5k"] for r in v]
        rho = spearman(xs, ys)
        pe = pearson(xs, ys)
        # p 值（近似）
        n = len(xs)
        tstat = rho * math.sqrt(max(1e-9, (n - 2) / max(1e-9, 1 - rho * rho)))
        within[ds] = {"n": n, "spearman": round(rho, 4), "pearson": round(pe, 4),
                      "t": round(tstat, 3)}
        print(f"  {ds:<16} n={n:<3} Spearman = {rho:+.4f}  Pearson = {pe:+.4f}  "
              f"t = {tstat:+.2f}")
    fm = fisher([within[ds]["spearman"] for ds in within])
    n_pos = sum(1 for ds in within if within[ds]["spearman"] > 0)
    print()
    print(f"  Fisher 平均组内相关 = **{fm:+.4f}** ｜ 为正的数据集 {n_pos}/{len(within)}")

    # ③ 池化对照
    print()
    print("=" * 92)
    print("③ 池化对照（看 Simpson 是否在 n=30 上仍在）")
    print("=" * 92)
    allx = [r["tau5"] for r in rows]
    ally = [r["top1_5k"] for r in rows]
    pooled = {"spearman": round(spearman(allx, ally), 4),
              "pearson": round(pearson(allx, ally), 4), "n": len(rows)}
    print(f"  池化 Spearman = {pooled['spearman']:+.4f}（n={len(rows)}）")
    print(f"  组内 Fisher  = {fm:+.4f}")
    print(f"  → 差 = {pooled['spearman'] - fm:+.4f}" +
          ("  🔴 仍存在 Simpson 悖论" if pooled["spearman"] - fm > 0.3 else ""))

    # ④ 数据集身份混杂
    print()
    print("=" * 92)
    print("④ 数据集身份混杂（n=30 版）")
    print("=" * 92)
    dsm = {}
    for ds in by:
        dsm[ds] = st.mean([r["top1_5k"] for r in by[ds]])
    dsmv = [dsm[r["dataset"]] for r in rows]
    print(f"  Spearman(τ, 数据集均值 top1) = {spearman(allx, dsmv):+.4f}")
    # 去均值
    tau_r, y_r = [], []
    for ds in by:
        mt = st.mean([r["tau5"] for r in by[ds]])
        my = dsm[ds]
        for r in by[ds]:
            tau_r.append(r["tau5"] - mt)
            y_r.append(r["top1_5k"] - my)
    resid = {"pearson": round(pearson(tau_r, y_r), 4),
             "spearman": round(spearman(tau_r, y_r), 4)}
    print(f"  **去数据集均值后** τ–top1：Pearson = {resid['pearson']:+.4f}  "
          f"Spearman = {resid['spearman']:+.4f}")

    # ⑤ 单 seed 内趋势（最干净的组内变异）
    print()
    print("=" * 92)
    print("⑤ 单 seed 内（同一训练轨迹的 epoch1–10）—— 最干净的组内检验")
    print("=" * 92)
    per_seed = {}
    for ds in sorted(by):
        for s in sorted({r["seed"] for r in by[ds]}):
            v = sorted([r for r in by[ds] if r["seed"] == s],
                       key=lambda r: r["epoch"])
            if len(v) < 5:
                continue
            xs = [r["tau5"] for r in v]
            ys = [r["top1_5k"] for r in v]
            rho = spearman(xs, ys)
            per_seed[f"{ds}|s{s}"] = round(rho, 4)
            print(f"  {ds:<14} seed{s:<4} n={len(v):<3} Spearman(τ,top1) = {rho:+.4f}  "
                  f"τ: {xs[0]:.4f}→{xs[-1]:.4f}  top1: {ys[0]:.2f}→{ys[-1]:.2f}")
    if per_seed:
        vals = [v for v in per_seed.values() if not math.isnan(v)]
        print()
        print(f"  单 seed 轨迹的 Fisher 平均 = **{fisher(vals):+.4f}**  ｜ "
              f"为正 {sum(1 for v in vals if v > 0)}/{len(vals)}")

    # ⑥ 判定
    print()
    print("=" * 92)
    print("⑥ 判定（决定标题）")
    print("=" * 92)
    good = fm > 0.3 and n_pos >= len(within) - 1
    if good:
        print(f"  ✅ 组内 τ 在 n=30 上为正（Fisher {fm:+.3f}）→ **τ 在组内有排序力**")
        print("     → 标题可用 'early-warning signal'")
    else:
        print(f"  🔴 组内 τ 未达正（Fisher {fm:+.3f}，为正 {n_pos}/{len(within)}）")
        print("     → **不能称监控器**；标题只应承诺「边界刻画」")
        print("     → 按 `docs/A1_REFRAME_PLAN.md` 的保守分支走")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": str(SRC.relative_to(REPO)), "n_checkpoints": len(rows),
             "within_spearman": within, "within_fisher": round(fm, 4),
             "pooled": pooled, "dataset_means": {k: round(v, 4) for k, v in dsm.items()},
             "dataset_identity_spearman": round(spearman(allx, dsmv), 4),
             "residual_after_removing_dataset_mean": resid,
             "per_seed_trajectory": per_seed,
             "per_seed_fisher": round(fisher(list(per_seed.values())), 4) if per_seed else None,
             "verdict": "tau_has_within_ranking_power" if good else "tau_lacks_within_ranking_power"},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
