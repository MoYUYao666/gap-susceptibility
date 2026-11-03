# -*- coding: utf-8 -*-
r"""用现有 COCO 补跑数据拟合 ODE，并**与旧表对照**（2026-10-08）。

## 背景（必须如实说明）

补跑协议（`experiments/strict_freeze_control.py`）产出的 `gap_history.json` 含
**`centroid_gap` / `distribution_gap`** 的逐 epoch 轨迹（epoch 0,1,2,4,6,8,10，**7 个点**），
**但不含 `dg_star`**（配对均方距离）——后者由**另一条实验路径**（`v1_trajectory`）写入
`dg_star_history.json`。

**而论文的 ODE 理论状态变量是 `dg_star`**（正文 Flickr30k 的拟合即用它）。
`dg_star` **无法从现有字段恢复**（`centroid_gap`/`distribution_gap`/`cosine_separation` 都不是它）。

**→ 本脚本只做一件事：算出"用现有可用轨迹能得到什么"，供操作者决定。**

## 输出

- 逐配置的 (α, β, R²)，基于 **`centroid_gap`** 轨迹（7 点）与 **`distribution_gap`** 轨迹；
- 与旧表（3 行，来源不明的 R² 0.897/0.910/0.966）并列对照。

    python tools\_p33_coco_ode_fit2.py [--apply]
"""
from __future__ import annotations

import collections
import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "coco_ode_from_gap_history.json"


def grid_fit(t, y):
    import numpy as np
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    if len(y) < 4:
        return float("nan"), float("nan"), float("nan")
    dg0 = float(y[0])
    r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t)
        den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        resid = float(((r - a * u) ** 2).sum())
        if resid < best[2]:
            best = (a * b, b, resid)
    A, B, _ = best
    yh = dg0 + (A / B) * (1.0 - np.exp(-B * t))
    ss = float(((y - y.mean()) ** 2).sum())
    R2 = 1.0 - float(((y - yh) ** 2).sum()) / ss if ss > 0 else float("nan")
    return A, B, R2


def main() -> int:
    apply = "--apply" in sys.argv
    fs = sorted(glob.glob(str(REPO / "outputs/coco_sweep/**/gap_history.json"), recursive=True))
    print(f"=== 找到 {len(fs)} 个 gap_history.json ===")
    rows = collections.defaultdict(lambda: collections.defaultdict(list))
    epochs_seen = set()
    for f in fs:
        parts = Path(f).parts
        rk, arm, seed = parts[-4], parts[-3], parts[-2]
        d = json.loads(io.open(f, encoding="utf-8").read())
        ep = d.get("epoch", [])
        epochs_seen.add(tuple(ep))
        for key in ("centroid_gap", "distribution_gap"):
            y = d.get(key)
            if y and len(y) >= 4:
                A, B, R2 = grid_fit(ep, y)
                rows[(arm, rk)][key].append((seed, A, B, R2))
    print(f"  epoch 网格: {sorted(epochs_seen)}")

    print("\n=== 逐配置拟合（3 seed 均值）===")
    print(f"  {'配置':<18} {'量':<18} {'α':>10} {'β':>9} {'R²':>8}  n")
    table = []
    for k in sorted(rows, key=lambda x: (x[0], int(x[1][1:]))):
        arm, rk = k
        for key in ("centroid_gap", "distribution_gap"):
            v = rows[k].get(key, [])
            if not v:
                continue
            As = [x[1] for x in v]; Bs = [x[2] for x in v]; Rs = [x[3] for x in v]
            print(f"  {arm + ' r=' + rk[1:]:<18} {key:<18} {st.mean(As):>+10.5f} "
                  f"{st.mean(Bs):>9.4f} {st.mean(Rs):>8.4f}  {len(v)}")
            table.append({"arm": arm, "rank": int(rk[1:]), "quantity": key, "n": len(v),
                          "alpha_mean": st.mean(As),
                          "alpha_sd": st.stdev(As) if len(As) > 1 else None,
                          "beta_mean": st.mean(Bs),
                          "beta_sd": st.stdev(Bs) if len(Bs) > 1 else None,
                          "r2_mean": st.mean(Rs)})

    print("\n=== 与旧表对照（旧表 3 行，来源不明的 R² 0.897/0.910/0.966）===")
    print("  旧表声称 R² ≈ 0.897–0.966；上表实测 R² 见上，可直接比较。")
    r2s = [t["r2_mean"] for t in table]
    if r2s:
        print(f"  本次实测 R² 范围：{min(r2s):.4f} – {max(r2s):.4f}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"table": table, "epoch_grids": [list(e) for e in epochs_seen],
                        "note": "基于 gap_history.json 的 centroid_gap/distribution_gap，"
                                "非 dg_star；dg_star 无法从现有字段恢复"},
                       ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
