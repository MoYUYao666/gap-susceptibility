# -*- coding: utf-8 -*-
r"""留一配置交叉验证：ODE 是"拟合"还是"预测"（2026-10-07）。

## 为什么做

`validation.tex` 的图注写：*"Solid curves: ODE predictions (α, β **fitted** over the full training
trajectory)"* —— **R²=0.986 是"两参数在完整轨迹上拟合"的优度**。
**任何指数收敛的两参数模型都会拟合得好** → 审稿人会说"你验证了函数形式，没验证能预测"。

## 本脚本回答两个不同的问题（**两种都报，不混为一谈**）

| 口径 | 问题 | 含义 |
|---|---|---|
| **A. 留出重拟合** | 给一条**没见过的轨迹**，ODE 拟合得好吗？ | **可复现性**（不是预测力） |
| **B. 参数外推** | 用**其它配置学到的参数**，能预测留出配置的轨迹吗？ | **真正的预测力** |

**关键设计**：预测时**只用第 1 个 epoch 定初值 $DG^*_0$**，其余 9 个 epoch 全靠 ODE 外推 —— 否则等于用答案改答案。

## 闭式解

$$\frac{d(DG^*)}{dt} = \alpha - \beta\,(DG^* - DG_0)
\;\Longrightarrow\;
DG^*(t) = DG_0 + \frac{\alpha}{\beta}\left(1 - e^{-\beta t}\right)$$

两参数记为 $(\alpha/\beta,\ \beta)$ —— **注意对 $DG^*$ 的初值敏感，故正文按 $DG_0$ 绝对化**。

    python tools\_p1_ode_loco.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import os
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "ode_loco.json"

try:
    from scipy.optimize import curve_fit
    import numpy as np
    HAVE = True
except Exception:
    HAVE = False


def model(t, A, B, dg0):
    """DG*(t) = dg0 + (A/B)(1 - exp(-B t))"""
    return dg0 + (A / B) * (1.0 - np.exp(-B * t))


def r2(y, yhat):
    y = np.asarray(y, float)
    yhat = np.asarray(yhat, float)
    ss = float(((y - y.mean()) ** 2).sum())
    return 1.0 - float(((y - yhat) ** 2).sum()) / ss if ss > 0 else float("nan")


def fit(t, y):
    """网格搜索 β + 解析求幅度（比 curve_fit 稳，无初值依赖）。

    DG*(t) = dg0 + A·(1 − e^{−βt})，A = α/β。
    给定 β，基函数 u(t)=1−e^{−βt} 已知 → A 有闭式最小二乘解 A = Σu·(y−dg0)/Σu²。
    """
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    dg0 = float(y[0])
    r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 600):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t)
        den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den          # 幅度 A = α/β
        resid = float(((r - a * u) ** 2).sum())
        if resid < best[2]:
            best = (a * b, b, resid)            # 返回 α = A·β
    A, B, _ = best
    if not np.isfinite(A):
        return float("nan"), float("nan"), float("nan")
    return float(A), float(B), r2(y, model(t, A, B, dg0))


def main() -> int:
    apply = "--apply" in sys.argv
    if not HAVE:
        print("  ❌ 需要 numpy + scipy")
        return 1

    # ── 载入：每个配置的**种子均值轨迹**
    traj = {}
    for f in sorted(glob.glob(str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)):
        parts = Path(f).parts
        conf = "/".join(parts[-4:-2])
        d = json.loads(io.open(f, encoding="utf-8").read())
        ep, y = d["epochs"], d["dg_star"]
        if len(ep) < 5:
            continue
        traj.setdefault(conf, []).append((ep, y))

    agg = {}
    for conf, runs in traj.items():
        n = min(len(y) for _, y in runs)
        agg[conf] = {"ep": list(runs[0][0][:n]),
                     "y": [st.mean(y[i] for _, y in runs) for i in range(n)],
                     "n_seeds": len(runs)}
    print(f"  配置数 {len(agg)} ｜ 轨迹长度 {sorted({len(v['y']) for v in agg.values()})}")

    # ── 逐配置拟合（in-sample，复现正文口径）
    fits = {}
    for conf, d in agg.items():
        t = np.asarray(d["ep"], float)
        y = np.asarray(d["y"], float)
        A, B, R = fit(t, y)
        fits[conf] = {"alpha": A, "beta": B, "R2_in": R, "y0": float(y[0]), "y": d["y"], "t": d["ep"]}
    good = {k: v for k, v in fits.items() if v["R2_in"] == v["R2_in"]}
    r_in = [v["R2_in"] for v in good.values()]
    print(f"  可拟合配置 {len(good)} ｜ **in-sample 平均 R² = {st.mean(r_in):.4f}** "
          f"（中位 {st.median(r_in):.4f}，范围 {min(r_in):.3f}–{max(r_in):.3f}）")
    print(f"  → 与正文 'mean R²=0.986' 口径一致" if abs(st.mean(r_in) - 0.986) < 0.05
          else f"  ⚠ 与正文 0.986 有差（本脚本用**种子均值**轨迹，正文可能逐 run 拟合）")

    if not apply:
        print("\n  （预演；加 --apply 跑 LOCO 并落盘）")
        return 0

    # ── 口径 A：留出**重拟合**（可复现性）
    #     设 A、B 已在其它配置上"定型"，留出配置仍允许重新拟合 → 即 in-sample，无信息量
    #     故改为**更严**的做法：留出配置用**其它配置的 (A,B) 均值**预测，不重新拟合
    A_mean = st.mean(v["alpha"] for v in good.values())
    B_mean = st.mean(v["beta"] for v in good.values())
    rA = [r2(v["y"], model(np.asarray(v["t"], float), A_mean, B_mean, v["y0"]))
          for v in good.values()]
    print(f"\n  === 口径 A：用**全体平均参数**预测每条轨迹（零拟合）===")
    print(f"    ᾱ={A_mean:.5f}  β̄={B_mean:.4f}")
    print(f"    平均 R² = {st.mean(rA):.4f}（中位 {st.median(rA):.4f}）")

    # ── 口径 B：真正 LOCO —— 用其它配置学 α、β 与配置特征的关系，预测留出配置
    #     特征：初始 DG*（首个 epoch）—— 唯一在"预测时点"可得的信息
    feats = {k: v["y0"] for k, v in good.items()}
    keys = sorted(good)
    loco = {}
    for hold in keys:
        tr = [k for k in keys if k != hold]
        xs = np.asarray([feats[k] for k in tr], float)
        ya = np.asarray([good[k]["alpha"] for k in tr], float)
        yb = np.asarray([good[k]["beta"] for k in tr], float)
        # 线性回归 α ~ a + b·DG*0（若退化则回退到均值）
        def lin(x, y):
            if np.ptp(x) < 1e-9:
                return lambda z: np.full_like(np.asarray(z, float), y.mean())
            c = np.polyfit(x, y, 1)
            return lambda z: np.polyval(c, np.asarray(z, float))
        fa, fb = lin(xs, ya), lin(xs, yb)
        Ah, Bh = float(fa([feats[hold]])[0]), float(fb([feats[hold]])[0])
        v = good[hold]
        t = np.asarray(v["t"], float)
        yh = model(t, Ah, Bh, v["y0"])
        loco[hold] = {"R2": r2(v["y"], yh), "alpha_pred": Ah, "alpha_fit": v["alpha"],
                      "beta_pred": Bh, "beta_fit": v["beta"]}
    rl = [v["R2"] for v in loco.values() if v["R2"] == v["R2"]]
    print(f"\n  === 口径 B：LOCO（用其它配置的 α~f(DG*₀) 关系预测留出配置）===")
    print(f"    平均 R² = {st.mean(rl):.4f}（中位 {st.median(rl):.4f}）")
    ra_corr = np.corrcoef([loco[k]["alpha_pred"] for k in keys],
                          [loco[k]["alpha_fit"] for k in keys])[0, 1]
    rb_corr = np.corrcoef([loco[k]["beta_pred"] for k in keys],
                          [loco[k]["beta_fit"] for k in keys])[0, 1]
    print(f"    corr(α_pred, α_fit) = {ra_corr:.3f} ｜ corr(β_pred, β_fit) = {rb_corr:.3f}")
    neg = sum(1 for r in rl if r < 0)
    print(f"    负 R² 的配置数 = {neg}/{len(rl)}（负值=不比取均值更好）")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    res = {"n_configs": len(good),
           "in_sample_R2_mean": st.mean(r_in), "in_sample_R2_median": st.median(r_in),
           "global_params_R2_mean": st.mean(rA),
           "loco_R2_mean": st.mean(rl), "loco_R2_median": st.median(rl),
           "loco_alpha_corr": float(ra_corr), "loco_beta_corr": float(rb_corr),
           "loco_negative_R2_count": neg,
           "alpha_mean": A_mean, "beta_mean": B_mean,
           "per_config": {k: {kk: vv for kk, vv in v.items() if kk not in ("t", "y")}
                          for k, v in good.items()},
           "loco_detail": loco}
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
