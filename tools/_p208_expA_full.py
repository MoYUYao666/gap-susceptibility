# -*- coding: utf-8 -*-
r"""E-A 完整版：留出检查点检验 + **全部 rival baseline**（解 FATAL 2）（2026-10-12）。

## 攻击点

论文用**池化** Spearman(τ, top-1) = 0.786 声称"秩序保持追踪准确率"，
但组内只有 −0.5 / −0.5 / +1.0 → **Simpson 悖论**；且**从未做留出预测检验**、
**没有 rival baseline**（审稿人原话）。

## 本实验

**数据**：`outputs/a1_h_offset.json:checkpoints`（13 个检查点）

**候选指标**（全部从同上字段取，逐条可复核）：

| 指标 | 字段 | 说明 |
|---|---|---|
| `tau` | `summary_tau5` | 本方法（秩序保持） |
| `cg` | `summary_CG_flickr` | **间隙**（论文说不能预测 zero-shot） |
| `abs_dx` | `displacement.mean_abs_dx` | **位移幅度**（rival baseline ①） |
| `text_dx` | `displacement.mean_abs_text_dx` | 文本侧位移（rival baseline ②） |
| `cos_gap` | `displacement.cos_shift_vs_gap_dir` | 位移与 gap 方向的对齐度 |
| `spread` | `geometry.within_class_spread_mean` | 类内散布 |
| `margin` | `geometry.margin_top1_mean` | top-1 margin |
| `jaccard` | `measured.top5_set_jaccard_vs_frozen` | top-5 集合与冻结的重合度 |

**三种留出**：LODO（留一数据集）｜LOS（留一 seed 组）
**判据**：留出 R²（相对常数基线）。**若 τ 不胜出 → 必须删/降级监控主张。**

    python tools\_p208_expA_full.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "a1_h_offset.json"
OUT = REPO / "outputs" / "analysis" / "a1_expA_full.json"


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


def r2(actual, pred):
    if len(actual) < 2:
        return float("nan")
    m = st.mean(actual)
    ss_res = sum((actual[i] - pred[i]) ** 2 for i in range(len(actual)))
    ss_tot = sum((a - m) ** 2 for a in actual)
    return 1 - ss_res / ss_tot if ss_tot else float("nan")


def fit_predict(xs, ys, xt):
    n = len(xs)
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return [my] * len(xt)
    b = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / sxx
    return [my - b * mx + b * x for x in xt]


SPECS = [
    ("tau", "summary_tau5", "本方法：秩序保持 τ₅"),
    ("cg", "summary_CG_flickr", "间隙 CG（论文称不能预测 zero-shot）"),
    ("abs_dx", "displacement.mean_abs_dx", "rival①：图像位移幅度"),
    ("text_dx", "displacement.mean_abs_text_dx", "rival②：文本位移幅度"),
    ("cos_gap", "displacement.cos_shift_vs_gap_dir", "位移与 gap 方向对齐度"),
    ("spread", "geometry.within_class_spread_mean", "类内散布"),
    ("margin", "geometry.margin_top1_mean", "top-1 margin"),
    ("jaccard", "measured.top5_set_jaccard_vs_frozen", "top-5 集合与冻结重合度"),
]


def dig(o, path):
    cur = o
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())
    cps = d["checkpoints"]

    rows = []
    for c in cps:
        r = {"tag": c.get("tag"), "dataset": c.get("dataset"),
             "top1": c.get("summary_top1_5k"), "seed": None}
        for name, path, _ in SPECS:
            r[name] = dig(c, path)
        # seed 从 tag 推
        t = str(c.get("tag", ""))
        r["seed"] = "seed43" if "seed43" in t else ("seed44" if "seed44" in t else "seed42/other")
        r["group"] = f"{r['dataset']}|{r['seed']}"
        rows.append(r)

    print("=" * 92)
    print(f"① 检查点（{len(rows)} 个，来源 outputs/a1_h_offset.json:checkpoints）")
    print("=" * 92)
    print(f"  {'tag':<30} {'ds':<12} {'tau':>8} {'cg':>8} {'abs_dx':>7} "
          f"{'text_dx':>7} {'spread':>8} {'margin':>9} {'top1':>7}")
    for r in rows:
        def f(x):
            return f"{x:.4f}" if isinstance(x, (int, float)) else "—"
        print(f"  {str(r['tag'])[:30]:<30} {str(r['dataset'])[:12]:<12} "
              f"{f(r['tau']):>8} {f(r['cg']):>8} {f(r['abs_dx']):>7} {f(r['text_dx']):>7} "
              f"{f(r['spread']):>8} {f(r['margin']):>9} {f(r['top1']):>7}")

    cands = [n for n, _, _ in SPECS
             if all(isinstance(r[n], (int, float)) for r in rows)]
    print(f"\n  全部检查点有值的指标: {cands}")

    # ② 池化 vs 组内
    print()
    print("=" * 92)
    print("② 池化 vs 组内（Simpson 检验）")
    print("=" * 92)
    pooled = {}
    for cand in cands:
        xs = [r[cand] for r in rows]
        ys = [r["top1"] for r in rows]
        pooled[cand] = {"pearson": round(pearson(xs, ys), 4),
                        "spearman": round(spearman(xs, ys), 4)}
        print(f"  {cand:<10} 池化 Pearson {pooled[cand]['pearson']:+.4f}  "
              f"Spearman {pooled[cand]['spearman']:+.4f}  (n={len(rows)})")
    print()
    by_ds, within = {}, {}
    for r in rows:
        by_ds.setdefault(r["dataset"], []).append(r)
    print("  ── 组内（每个数据集内，跨 seed）──")
    for ds, rs in sorted(by_ds.items()):
        if len(rs) < 3:
            print(f"    {ds:<14} n={len(rs)}（<3，跳过）")
            continue
        res = {}
        for cand in cands:
            xs = [r[cand] for r in rs]
            ys = [r["top1"] for r in rs]
            res[cand] = round(spearman(xs, ys), 4)
        within[ds] = res
        print(f"    {ds:<14} n={len(rs)}  " + "  ".join(
            f"{c}={res[c]:+.2f}" for c in cands))

    # ③ 留出
    print()
    print("=" * 92)
    print("③ 留一数据集（LODO）留出 R²")
    print("=" * 92)
    lodo = {c: {} for c in cands}
    for held in sorted(by_ds):
        tr = [r for r in rows if r["dataset"] != held]
        te = [r for r in rows if r["dataset"] == held]
        if len(tr) < 4 or len(te) < 2:
            continue
        print(f"\n  留出 {held}（训练 n={len(tr)}，测试 n={len(te)}）")
        for cand in cands:
            xs = [r[cand] for r in tr]
            ys = [r["top1"] for r in tr]
            at = [r["top1"] for r in te]
            pred = fit_predict(xs, ys, [r[cand] for r in te])
            const = [st.mean(ys)] * len(te)
            lodo[cand][held] = {"r2_linear": round(r2(at, pred), 4),
                                "r2_const": round(r2(at, const), 4)}
            flag = "✅" if lodo[cand][held]["r2_linear"] > 0 else "  "
            print(f"    {flag} {cand:<10} R²={lodo[cand][held]['r2_linear']:+12.4f}  "
                  f"（常数基线 {lodo[cand][held]['r2_const']:+.4f}）")

    print()
    print("=" * 92)
    print("④ 汇总排名（平均留出 R²；>0 才优于「预测训练集均值」）")
    print("=" * 92)
    summary = {}
    for cand in cands:
        v = [x["r2_linear"] for x in lodo[cand].values()]
        if not v:
            continue
        summary[cand] = {"mean_r2": round(st.mean(v), 4),
                         "median_r2": round(st.median(v), 4),
                         "wins_positive": sum(1 for x in v if x > 0),
                         "n_folds": len(v),
                         "beats_const": sum(1 for x in lodo[cand].values()
                                            if x["r2_linear"] > x["r2_const"])}
    order = sorted(summary, key=lambda c: -summary[c]["mean_r2"])
    print(f"  {'指标':<10} {'平均留出R²':>12} {'中位':>10} {'>0折':>6} {'优于常数':>9}")
    for c in order:
        s = summary[c]
        print(f"  {c:<10} {s['mean_r2']:>12.4f} {s['median_r2']:>10.4f} "
              f"{s['wins_positive']}/{s['n_folds']:>3} {s['beats_const']}/{s['n_folds']:>5}")
    print()
    print(f"  排名第一: **{order[0]}**")
    if order[0] != "tau":
        print(f"  🔴 τ 不是第一（τ 排第 {order.index('tau') + 1}/{len(order)}）")
    if summary.get("tau", {}).get("mean_r2", -1) <= 0:
        print(f"  🔴 τ 的平均留出 R² = {summary['tau']['mean_r2']:+.4f} ≤ 0 "
              f"→ **在新数据集上不如直接猜训练集均值**")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": "outputs/a1_h_offset.json:checkpoints",
             "field_map": {n: p for n, p, _ in SPECS},
             "n_checkpoints": len(rows), "candidates": cands,
             "pooled": pooled, "within_dataset": within, "lodo": lodo,
             "summary": summary, "ranking": order},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
