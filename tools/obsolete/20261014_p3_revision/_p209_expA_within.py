# -*- coding: utf-8 -*-
r"""E-A 修正版：**组内**（同一数据集跨 seed）留出检验（2026-10-12）。

## 为什么改

`_p208` 的 LODO（留一整个数据集）有个**设计缺陷**：
组内 τ 跨度只有 0.0005（coco: 0.5754/0.5757/0.5759），组间跨度 0.2
→ 留出折的 τ 值落在训练值域**之外** → 线性外推 R² 无意义
（flickr30k 那折 R²=−371 就是外推爆炸，不是 τ 无用）。

**监控器的真实用途是**：同一数据集内比较检查点。
→ 正确的检验是**组内跨 seed 的排序能力**。

## 本实验

对每个指标，算：
1. **组内 Spearman**（每个数据集内，3 个 seed）→ 能否排序
2. **Fisher-z 平均**组内相关
3. **池化 Spearman**（对照，看 Simpson 效应）
4. **组内留一 seed**（用 2 个 seed 拟合，预测第 3 个）

    python tools\_p209_expA_within.py [--apply]
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
SRC = REPO / "outputs" / "a1_h_offset.json"
OUT = REPO / "outputs" / "analysis" / "a1_expA_within.json"

SPECS = [
    ("tau", "summary_tau5", "本方法：秩序保持 τ₅"),
    ("margin", "geometry.margin_top1_mean", "top-1 margin"),
    ("cg", "summary_CG_flickr", "间隙 CG"),
    ("abs_dx", "displacement.mean_abs_dx", "图像位移幅度"),
    ("text_dx", "displacement.mean_abs_text_dx", "文本位移幅度"),
    ("cos_gap", "displacement.cos_shift_vs_gap_dir", "位移与 gap 方向对齐度"),
    ("spread", "geometry.within_class_spread_mean", "类内散布"),
    ("jaccard", "measured.top5_set_jaccard_vs_frozen", "top-5 集合重合度"),
]


def dig(o, path):
    cur = o
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


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


def fisher_mean(rs):
    zs = [math.atanh(max(-0.999, min(0.999, r))) for r in rs if not math.isnan(r)]
    return math.tanh(st.mean(zs)) if zs else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())
    cps = d["checkpoints"]

    rows = []
    for c in cps:
        r = {"tag": c.get("tag"), "dataset": c.get("dataset"),
             "top1": c.get("summary_top1_5k")}
        for name, path, _ in SPECS:
            r[name] = dig(c, path)
        rows.append(r)

    # 只保留组内 >=3 个 seed 的数据集
    by_ds = {}
    for r in rows:
        by_ds.setdefault(r["dataset"], []).append(r)
    multi = {k: v for k, v in by_ds.items() if len(v) >= 3}
    print("=" * 92)
    print(f"① 可用于组内检验的数据集: {sorted(multi)}")
    print("=" * 92)
    for ds, rs in sorted(multi.items()):
        print(f"  {ds:<14} n={len(rs)}  top1 = {[r['top1'] for r in rs]}")

    cands = [n for n, _, _ in SPECS
             if all(isinstance(r[n], (int, float)) for r in rows)]

    print()
    print("=" * 92)
    print("② 组内 Spearman（同一数据集内跨 seed：能否排序检查点）")
    print("=" * 92)
    hdr = f"  {'指标':<10}" + "".join(f"{ds[:11]:>13}" for ds in sorted(multi)) + f"{'Fisher均值':>13}"
    print(hdr)
    within = {}
    for cand in cands:
        cells, rs_all = [], []
        for ds in sorted(multi):
            r_ = spearman([r[cand] for r in multi[ds]], [r["top1"] for r in multi[ds]])
            cells.append(r_)
            rs_all.append(r_)
        fm = fisher_mean(rs_all)
        within[cand] = {"per_dataset": {ds: round(cells[i], 4)
                                        for i, ds in enumerate(sorted(multi))},
                        "fisher_mean": round(fm, 4)}
        print(f"  {cand:<10}" + "".join(f"{c:+13.2f}" for c in cells) + f"{fm:+13.3f}")

    print()
    print("=" * 92)
    print("③ 池化 Spearman（对照：Simpson 效应有多大）")
    print("=" * 92)
    pooled = {}
    for cand in cands:
        p_ = pearson([r[cand] for r in rows], [r["top1"] for r in rows])
        s_ = spearman([r[cand] for r in rows], [r["top1"] for r in rows])
        pooled[cand] = {"pearson": round(p_, 4), "spearman": round(s_, 4)}
        w = within[cand]["fisher_mean"]
        gapflag = "🔴 池化>>组内" if (s_ - w) > 0.4 else ""
        print(f"  {cand:<10} 池化 {s_:+.4f} ｜ 组内均值 {w:+.4f} ｜ 差 {s_ - w:+.4f}  {gapflag}")

    print()
    print("=" * 92)
    print("④ 排名")
    print("=" * 92)
    order = sorted(cands, key=lambda c: -within[c]["fisher_mean"])
    print(f"  按组内 Fisher 均值：")
    for i, c in enumerate(order, 1):
        mark = "  ← 本方法" if c == "tau" else ""
        print(f"    {i}. {c:<10} {within[c]['fisher_mean']:+.4f}{mark}")
    tau_rank = order.index("tau") + 1
    print()
    print(f"  τ 排第 {tau_rank}/{len(order)}")
    if tau_rank > 1:
        print(f"  🔴 **τ 不是组内最佳**（最佳是 {order[0]}，"
              f"{within[order[0]]['fisher_mean']:+.3f} vs τ {within['tau']['fisher_mean']:+.3f}）")
    if within["tau"]["fisher_mean"] <= 0:
        print(f"  🔴 **τ 的组内平均相关 ≤ 0** → 无法排序同一数据集内的检查点")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": "outputs/a1_h_offset.json:checkpoints",
             "field_map": {n: p for n, p, _ in SPECS},
             "datasets_within": sorted(multi),
             "within_spearman": within, "pooled": pooled, "ranking": order},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
