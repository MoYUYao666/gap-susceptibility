# -*- coding: utf-8 -*-
r"""COCO 上 **DG\\* 与 CG 脱节**的核实（2026-10-08 18:40）。

## 观察

| run | CGΔ | DG\\* 跨度 |
|---|---|---|
| 新跑（严格冻结）`r4/both` seed42 | **−0.0898** | **0.0061** |
| 新跑（严格冻结）`r4/both` seed123 | （同量级） | **0.0032** |
| 归档 `coco_both_r8`（**非严格冻结**，1.45 亿参数） | — | **0.1011** |

**→ 在同一 run 里，CG 明显收窄，而 DG\\* 几乎不动。**

## 本脚本回答

1. 对现有新跑轨迹拟合 ODE，看 **R² 与 α 的可用性**；
2. 与**同数据集的 CG 轨迹拟合**对照（CG 的 R² 明显更高）；
3. 判断"用 DG\\* 拟合 COCO"是否可行，供操作者决定是否让 34 个 run 继续跑。

    python tools\_p38_coco_dgstar_check.py
"""
from __future__ import annotations

import glob
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


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
    print("=== 新跑（严格冻结）DG* vs CG/empirical 的拟合对比 ===")
    print(f"  {'run':<22} {'量':<16} {'α':>10} {'β':>9} {'R²':>8}  跨度")
    for f in sorted(glob.glob(str(REPO / "outputs/coco_sweep_dgstar/**/dg_star_history.json"),
                              recursive=True)):
        parts = Path(f).parts
        tag = f"{parts[-4]}/{parts[-3]}/{parts[-2]}"
        d = json.loads(io.open(f, encoding="utf-8").read())
        for key in ("dg_star", "cg", "dg_empirical"):
            y = d.get(key)
            if not y:
                continue
            A, B, R2 = grid_fit(d["epochs"], y)
            print(f"  {tag:<22} {key:<16} {A:>+10.5f} {B:>9.5f} {R2:>8.4f}  "
                  f"{max(y)-min(y):.4f}")

    print("\n=== 对照：归档 COCO（非严格冻结，10 点）===")
    for f in sorted(glob.glob(str(REPO / "outputs/theory/coco/coco_both_r8/seed*/dg_star_history.json"))):
        d = json.loads(io.open(f, encoding="utf-8").read())
        A, B, R2 = grid_fit(d["epochs"], d["dg_star"])
        y = d["dg_star"]
        print(f"  {Path(f).parts[-2]:<22} {'dg_star':<16} {A:>+10.5f} {B:>9.5f} {R2:>8.4f}  "
              f"{max(y)-min(y):.4f}")

    print("\n=== 对照：归档 Flickr30k（严格冻结，10 点）===")
    for f in sorted(glob.glob(str(REPO / "outputs/theory/v1_trajectory/v1_both_r8/seed*/dg_star_history.json"))):
        d = json.loads(io.open(f, encoding="utf-8").read())
        A, B, R2 = grid_fit(d["epochs"], d["dg_star"])
        y = d["dg_star"]
        print(f"  {Path(f).parts[-2]:<22} {'dg_star':<16} {A:>+10.5f} {B:>9.5f} {R2:>8.4f}  "
              f"{max(y)-min(y):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
