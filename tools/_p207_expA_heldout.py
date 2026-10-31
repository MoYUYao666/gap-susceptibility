# -*- coding: utf-8 -*-
r"""E-A：留出检查点检验 + rival baseline（解 FATAL 2）（2026-10-12）。

## 攻击点（`docs/A1_ADVERSARIAL_METHOD.md` §2 / C1）

论文用**池化** Spearman(τ, top-1) = 0.786 声称"秩序保持追踪准确率"，
但**组内**只有 −0.5（COCO）/ −0.5（Food-101）/ +1.0（DTD）→ **Simpson 悖论**。
而且"从未做留出预测检验"，"没有 rival baseline"。

## 本实验（**只算，不改论文**）

数据：`outputs/a1_h_offset.json` 的 `checkpoints`（13 个，每个含
`summary_tau5` / `summary_top1_5k` / `summary_CG_*` / `dataset`）。

**三种检验**（每种都对所有候选指标做，看谁在**留出**上更准）：

| 检验 | 留出单位 | 问题 |
|---|---|---|
| **LODO** | 整个数据集 | 能否把在一个数据集上学到的映射用到**没见过的数据集** |
| **LOVO** | vision 塔配置（`by_vision_tower`） | 能否跨骨干迁移 |
| **LOS** | 单个 seed 组 | —— |

**rival baselines**（与 τ 同样做留出预测）：
`CG`（间隙）、`displacement`（位移）、`tau`（本方法）、常数基线（预测训练集均值）。

**判据**：留出 R²。**若 τ 不胜出，就必须删除"监控"主张**（审稿人的 diagnosis）。

    python tools\_p207_expA_heldout.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "a1_expA_heldout.json"


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
    """最小二乘一元线性；返回对 xt 的预测。"""
    n = len(xs)
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return [my] * len(xt)
    b = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / sxx
    a = my - b * mx
    return [a + b * x for x in xt]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())
    cps = d["checkpoints"]
    print("=" * 90)
    print(f"① 检查点（共 {len(cps)} 个，来源 outputs/a1_h_offset.json:checkpoints）")
    print("=" * 90)
    rows = []
    for c in cps:
        r = {
            "tag": c.get("tag"), "dataset": c.get("dataset"),
            "tau": c.get("summary_tau5"),
            "top1": c.get("summary_top1_5k"),
            "CG": (c.get("summary_CG_flickr_val") or c.get("summary_CG")
                   or c.get("summary_cg")),
            "vision_lora": c.get("vision_lora"), "text_lora": c.get("text_lora"),
        }
        # 找位移类字段
        for k, v in c.items():
            if "displ" in k.lower() or "norm" in k.lower():
                r[k] = v
        rows.append(r)
    keys = sorted({k for r in rows for k in r})
    for r in rows:
        print(f"  {str(r['tag'])[:30]:<30} ds={str(r['dataset'])[:11]:<11} "
              f"tau={r['tau']} top1={r['top1']} CG={r['CG']}")
    print(f"\n  可用字段: {keys}")

    have_tau = [r for r in rows if isinstance(r["tau"], (int, float))]
    have_top = [r for r in rows if isinstance(r["top1"], (int, float))]
    print(f"  有 tau: {len(have_tau)} ｜ 有 top1: {len(have_top)}")

    # 候选指标（有值的）
    CANDS = []
    for name in ("tau", "CG"):
        if all(isinstance(r[name], (int, float)) for r in rows):
            CANDS.append(name)
    for k in keys:
        if k.startswith("summary_") and k not in ("summary_tau5", "summary_top1_5k",
                                                  "summary_top1_50k") and \
                all(isinstance(r.get(k), (int, float)) for r in rows):
            CANDS.append(k)
    print(f"  候选指标（全检查点有值）: {CANDS}")

    # ══════════ 池化 vs 组内 ══════════
    print()
    print("=" * 90)
    print("② 池化 vs 组内相关（复现审稿人的 Simpson 结论）")
    print("=" * 90)
    pooled = {}
    for cand in CANDS:
        xs = [r[cand] for r in rows]
        ys = [r["top1"] for r in rows]
        pooled[cand] = {"pearson": round(pearson(xs, ys), 4),
                        "spearman": round(spearman(xs, ys), 4)}
        print(f"  池化 {cand:<26} Pearson {pooled[cand]['pearson']:+.4f}  "
              f"Spearman {pooled[cand]['spearman']:+.4f}  (n={len(rows)})")
    print()
    by_ds = {}
    for r in rows:
        by_ds.setdefault(r["dataset"], []).append(r)
    for ds, rs in sorted(by_ds.items()):
        if len(rs) < 3:
            continue
        xs = [r["tau"] for r in rs]
        ys = [r["top1"] for r in rs]
        by_ds[ds] = {"n": len(rs), "spearman_tau_top1": round(spearman(xs, ys), 4),
                     "tau": [r["tau"] for r in rs], "top1": [r["top1"] for r in rs]}
        print(f"  组内 {ds:<14} n={len(rs)}  Spearman(tau, top1) = "
              f"{by_ds[ds]['spearman_tau_top1']:+.4f}   tau={by_ds[ds]['tau']}  "
              f"top1={by_ds[ds]['top1']}")

    # ══════════ 留出检验 ══════════
    print()
    print("=" * 90)
    print("③ 留出检验：留一数据集（LODO）")
    print("=" * 90)
    datasets = sorted({r["dataset"] for r in rows})
    lodo = {c: {} for c in CANDS}
    for held in datasets:
        tr = [r for r in rows if r["dataset"] != held]
        te = [r for r in rows if r["dataset"] == held]
        if len(tr) < 3 or len(te) < 2:
            continue
        print(f"\n  留出 {held}（测试 n={len(te)}，训练 n={len(tr)}）")
        for cand in CANDS:
            xs = [r[cand] for r in tr]
            ys = [r["top1"] for r in tr]
            xt = [r[cand] for r in te]
            at = [r["top1"] for r in te]
            pred = fit_predict(xs, ys, xt)
            const = [st.mean(ys)] * len(te)
            lodo[cand][held] = {"r2_linear": round(r2(at, pred), 4),
                                "r2_const": round(r2(at, const), 4),
                                "pred": [round(p, 3) for p in pred],
                                "actual": at}
            print(f"    {cand:<26} R²(linear)={lodo[cand][held]['r2_linear']:+.4f}  "
                  f"R²(常数基线)={lodo[cand][held]['r2_const']:+.4f}")

    print()
    print("=" * 90)
    print("④ 汇总：每个指标的平均留出 R²（越高越好；>0 才优于常数）")
    print("=" * 90)
    summary = {}
    for cand in CANDS:
        vals = [v["r2_linear"] for v in lodo[cand].values()]
        consts = [v["r2_const"] for v in lodo[cand].values()]
        if not vals:
            continue
        summary[cand] = {"mean_r2": round(st.mean(vals), 4),
                         "mean_r2_const": round(st.mean(consts), 4),
                         "wins": sum(1 for v in vals if v > 0),
                         "n_folds": len(vals)}
        print(f"  {cand:<28} 平均留出 R² = {summary[cand]['mean_r2']:+.4f}  "
              f"｜常数基线 {summary[cand]['mean_r2_const']:+.4f}  "
              f"｜{summary[cand]['wins']}/{summary[cand]['n_folds']} 折优于常数")

    best = max(summary, key=lambda c: summary[c]["mean_r2"]) if summary else None
    print()
    print("=" * 90)
    print("⑤ 判定")
    print("=" * 90)
    print(f"  最佳指标: {best}（平均留出 R² = {summary[best]['mean_r2']:+.4f}）"
          if best else "  无法判定")
    if best and best != "tau":
        print(f"  🔴 **tau 不是最佳** → 按审稿人的判据，**必须删除/降级监控主张**")
    elif best == "tau":
        print(f"  ⚠️ tau 最佳，但平均留出 R² = {summary['tau']['mean_r2']:+.4f}；"
              f"若 ≤0 则仍未优于常数基线")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": "outputs/a1_h_offset.json:checkpoints", "n_checkpoints": len(rows),
             "candidates": CANDS, "pooled": pooled, "within_dataset": by_ds,
             "lodo": lodo, "summary": summary, "best": best},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
