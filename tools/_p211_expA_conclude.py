# -*- coding: utf-8 -*-
r"""E-A 结论固化：τ 的池化 vs 组内（全部出自论文归档）（2026-10-12）。

## 已确认（`tools/_p209`、`_p210`）

| 检验 | τ | CG |
|---|---|---|
| **池化**（n=13 检查点） | **+0.75** | +0.29 |
| **组内**（4 数据集 × 3 seed） | **−0.27**（Fisher 均值） | +0.97 |
| 论文归档 `within_dataset_rank_check` | −0.5 / +1.0 / −0.5 | +1.0 / +0.5 / +0.5 |

**→ 池化相关中 τ 强、CG 弱；组内恰好相反 → Simpson 悖论。**

## 本脚本

1. 读全 `cross_checkpoint_correlations`（论文自己的池化数）
2. 验证 `margin` 是否为"按构造"与 top-1 相关（避免把它当公平 rival）
3. 固化结论 JSON

    python tools\_p211_expA_conclude.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S1 = REPO / "outputs" / "a1_h_seed_summary.json"
S2 = REPO / "outputs" / "a1_h_offset.json"
OUT = REPO / "outputs" / "analysis" / "a1_expA_conclusion.json"


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}

    d1 = json.loads(io.open(S1, encoding="utf-8", errors="replace").read())
    print("=" * 92)
    print("① 论文自己的池化相关（cross_checkpoint_correlations）")
    print("=" * 92)
    ccc = d1.get("cross_checkpoint_correlations", {})
    for name, v in ccc.items():
        if not isinstance(v, dict):
            continue
        print(f"\n  ── {name}（n={v.get('n')}）──")
        for k, x in v.items():
            if isinstance(x, dict):
                print(f"     {k}: {json.dumps(x, ensure_ascii=False)[:200]}")
            elif k not in ("label", "tags", "datasets", "n"):
                print(f"     {k}: {x}")
        res[name] = {k: x for k, x in v.items() if isinstance(x, (int, float, str))}

    print()
    print("=" * 92)
    print("② margin 是否为「按构造」相关（决定它能否作为公平 rival）")
    print("=" * 92)
    d2 = json.loads(io.open(S2, encoding="utf-8", errors="replace").read())
    rows = []
    for c in d2["checkpoints"]:
        g = c.get("geometry", {})
        rows.append({"tag": c.get("tag"), "dataset": c.get("dataset"),
                     "top1": c.get("summary_top1_5k"),
                     "margin": g.get("margin_top1_mean"),
                     "frac_correct": g.get("frac_correct_top1")})
    print("  margin_top1_mean vs top1 的关系（逐检查点）")
    print(f"  {'tag':<30} {'margin':>10} {'frac_correct':>13} {'top1':>7}")
    for r in rows:
        print(f"  {str(r['tag'])[:30]:<30} {r['margin']:>10.5f} "
              f"{r['frac_correct']:>13.4f} {r['top1']:>7}")
    ms = [r["margin"] for r in rows]
    ts = [r["top1"] for r in rows]
    fc = [r["frac_correct"] for r in rows]
    print(f"\n  Pearson(margin, top1) = {pearson(ms, ts):+.4f}")
    print(f"  Pearson(frac_correct, top1) = {pearson(fc, ts):+.4f}")
    print("  → frac_correct_top1 = 正确类的占比 = top1/100 **按定义**")
    print("  → margin 是「正确类得分」的均值，与准确率近乎同义（不是独立的 rival baseline）")
    res["margin_pearson_top1"] = round(pearson(ms, ts), 4)
    res["frac_correct_pearson_top1"] = round(pearson(fc, ts), 4)

    print()
    print("=" * 92)
    print("③ 结论（全部可复核）")
    print("=" * 92)
    wd = d1.get("within_dataset_rank_check", {})
    res["within_from_archive"] = {k: {kk: vv for kk, vv in v.items()
                                      if "spearman" in kk}
                                  for k, v in wd.items() if isinstance(v, dict)}
    print("  τ：池化强(+0.75) 但组内反向(−0.5/+1.0/−0.5)")
    print("  CG：池化弱(+0.29) 但组内一致为正(+1.0/+0.5/+0.5)")
    print("  → **池化相关的方向与组内相反 = Simpson 悖论**")
    print("  → τ 不能排序同一数据集内的检查点；CG 可以")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
