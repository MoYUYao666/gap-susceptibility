# -*- coding: utf-8 -*-
r"""验证：池化的 τ–top1 相关是否由「数据集身份」承载（2026-10-12）。

## 假说

τ 的池化相关（+0.85～+1.00）与组内相关（−0.27）方向相反 →
**假说**：池化相关其实在测"这个检查点属于哪个数据集"，而不是"秩序保持得好不好"。

## 检验（用论文自己的归档 `a1_h_seed_summary.json` 的池化数据）

1. 对每个检查点，其**数据集均值 top-1** 与 τ 的相关
   （若 τ 与数据集身份几乎共线 → 池化相关无独立信息）
2. **去掉数据集均值后**的 τ–top1 相关（= 组内相关之和）
3. **τ 与数据集身份的可分性**：用 τ 能否判断检查点属于哪个数据集

    python tools\_p216_verify_dataset_confound.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "a1_dataset_confound.json"


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())

    rows = [{"ds": c.get("dataset"), "tau": c.get("summary_tau5"),
             "top1": c.get("summary_top1_5k")} for c in d["checkpoints"]]
    rows = [r for r in rows if isinstance(r["tau"], (int, float))
            and isinstance(r["top1"], (int, float))]
    print("=" * 88)
    print(f"检查点 {len(rows)} 个（来源 outputs/a1_h_offset.json:checkpoints）")
    print("=" * 88)

    # 数据集均值
    means = {}
    for r in rows:
        means.setdefault(r["ds"], []).append(r["top1"])
    ds_mean = {k: st.mean(v) for k, v in means.items()}
    print("  各数据集 top-1 均值（这就是「数据集身份」的数值代理）:")
    for k in sorted(ds_mean):
        print(f"    {k:<16} {ds_mean[k]:.3f}  (n={len(means[k])})")

    tau = [r["tau"] for r in rows]
    top1 = [r["top1"] for r in rows]
    dsm = [ds_mean[r["ds"]] for r in rows]

    print()
    print("=" * 88)
    print("检验")
    print("=" * 88)
    r_tau_top1 = pearson(tau, top1)
    r_tau_dsm = pearson(tau, dsm)
    r_dsm_top1 = pearson(dsm, top1)
    print(f"  ① τ  vs top1         Pearson = {r_tau_top1:+.4f}   （池化，论文引用的那种）")
    print(f"  ② τ  vs 数据集均值    Pearson = {r_tau_dsm:+.4f}   ← τ 与「数据集身份」的共线度")
    print(f"  ③ 数据集均值 vs top1  Pearson = {r_dsm_top1:+.4f}   （按构造应很高）")

    # 去掉数据集均值后
    t_res = [tau[i] - st.mean([r["tau"] for r in rows if r["ds"] == rows[i]["ds"]])
             for i in range(len(rows))]
    y_res = [top1[i] - ds_mean[rows[i]["ds"]] for i in range(len(rows))]
    r_res = pearson(t_res, y_res)
    print(f"  ④ **去数据集均值后** τ vs top1 = {r_res:+.4f}  ← 组内信号（应≈组内均值）")
    print()
    print(f"  → 池化 {r_tau_top1:+.3f} 中有多少来自数据集身份？")
    print(f"     若 τ 与数据集身份几乎共线（②接近 ±1）→ 池化相关主要是身份效应")

    # 可分性：τ 能否区分数据集
    print()
    print("=" * 88)
    print("可分性：τ 的取值范围能否区分数据集")
    print("=" * 88)
    rng = {}
    for r in rows:
        rng.setdefault(r["ds"], []).append(r["tau"])
    for k in sorted(rng):
        v = rng[k]
        print(f"  {k:<16} τ ∈ [{min(v):.4f}, {max(v):.4f}]  跨度 {max(v) - min(v):.4f}")

    # 数值验证：数据集身份能否只靠 τ 判断
    print()
    print("  Spearman(τ, 数据集均值) =", f"{spearman(tau, dsm):+.4f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": "outputs/a1_h_offset.json:checkpoints",
             "n": len(rows),
             "pearson_tau_top1_pooled": round(r_tau_top1, 4),
             "pearson_tau_datasetmean": round(r_tau_dsm, 4),
             "pearson_datasetmean_top1": round(r_dsm_top1, 4),
             "pearson_tau_top1_within_residual": round(r_res, 4),
             "dataset_top1_means": {k: round(v, 4) for k, v in ds_mean.items()},
             "tau_ranges": {k: [round(min(v), 4), round(max(v), 4)]
                            for k, v in rng.items()}},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
