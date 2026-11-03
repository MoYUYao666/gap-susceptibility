# -*- coding: utf-8 -*-
r"""核实「COCO + 严格冻结」下 `DG*` 是否**普遍失效**（2026-10-08 18:45）。

## 为什么要核实

新跑 `r4/both` 两个 seed 的 `DG*` 拟合 R² 只有 **0.124 / 0.679**，
而同一 run 的 `cg` 是 **0.927 / 0.931**。

**若这是普遍现象 → 剩 34 个 run 跑完也拟合不出可用的 `DG*` → 应停。**
**若只是 r4 的偶发 → 应继续。**

## 本脚本

对**全部 31 个旧跑**（严格冻结、无 `dg_star`）的 `cg` 轨迹与
**2 个新跑**的 `dg_star` 轨迹做系统对比，并检查：
`dg_star` 的失效是否与 rank 有关。

**注意**：旧跑没记 `dg_star`，故用 `cg` 作为"这个 run 是否真的在动"的指示；
新跑两者都有，可直接算二者跨度之比。

    python tools\_p39_verify_dgstar_failure.py
"""
from __future__ import annotations

import collections
import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def grid_fit(t, y):
    import numpy as np
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    if len(y) < 4:
        return float("nan"), float("nan")
    dg0 = float(y[0])
    r = y - dg0
    best = (float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t)
        den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        resid = float(((r - a * u) ** 2).sum())
        if resid < best[1]:
            best = (a * b, resid)
    A = best[0]
    B = None
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t)
        den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        if abs(a * b - A) < 1e-9:
            B = b
            break
    yh = dg0 + (A / B) * (1.0 - np.exp(-B * t)) if B else y
    ss = float(((y - y.mean()) ** 2).sum())
    R2 = 1.0 - float(((y - yh) ** 2).sum()) / ss if ss > 0 else float("nan")
    return A, R2


def main() -> int:
    print("=== ① 旧跑 31 个（严格冻结）的 cg 轨迹健康度 ===")
    byconf = collections.defaultdict(list)
    for f in sorted(glob.glob(str(REPO / "outputs/coco_sweep/**/gap_history.json"), recursive=True)):
        parts = Path(f).parts
        byconf[(parts[-3], parts[-4])].append(Path(f))
    print(f"  {'配置':<20} {'n':>3} {'cg 跨度':>9} {'cg R²':>8}")
    for k in sorted(byconf, key=lambda x: (x[0], int(x[1][1:]))):
        spans, r2s = [], []
        for f in byconf[k]:
            d = json.loads(io.open(f, encoding="utf-8").read())
            y = d.get("centroid_gap", [])
            if y:
                spans.append(max(y) - min(y))
                _, R2 = grid_fit(d.get("epoch") or d.get("epochs"), y)
                r2s.append(R2)
        if spans:
            print(f"  {'%s r=%s' % k:<20} {len(spans):>3} {st.mean(spans):>9.4f} {st.mean(r2s):>8.4f}")

    print("\n=== ② 新跑 2 个：dg_star 与 cg 的跨度之比 ===")
    print(f"  {'run':<22} {'dg* 跨度':>10} {'cg 跨度':>10} {'比值':>8} {'dg* R²':>8} {'cg R²':>8}")
    for f in sorted(glob.glob(str(REPO / "outputs/coco_sweep_dgstar/**/dg_star_history.json"),
                              recursive=True)):
        parts = Path(f).parts
        d = json.loads(io.open(f, encoding="utf-8").read())
        ds, cg = d.get("dg_star", []), d.get("cg", [])
        if not ds or not cg:
            continue
        _, r2d = grid_fit(d.get("epochs") or d.get("epoch"), ds)
        _, r2c = grid_fit(d.get("epochs") or d.get("epoch"), cg)
        sd, sc = max(ds) - min(ds), max(cg) - min(cg)
        print(f"  {parts[-4] + '/' + parts[-3] + '/' + parts[-2]:<22} {sd:>10.4f} {sc:>10.4f} "
              f"{sd/sc:>8.3f} {r2d:>8.4f} {r2c:>8.4f}")

    print("\n=== ③ 对照：Flickr30k 严格冻结下 dg* 与 cg 的关系 ===")
    print("  （归档只有 dg_star 与 cg 两条序列）")
    for f in sorted(glob.glob(str(REPO / "outputs/theory/v1_trajectory/v1_both_r8/seed*/dg_star_history.json")))[:2]:
        d = json.loads(io.open(f, encoding="utf-8").read())
        ds, cg = d.get("dg_star", []), d.get("cg", [])
        if ds and cg:
            sd, sc = max(ds) - min(ds), max(cg) - min(cg)
            _, r2d = grid_fit(d.get("epochs") or d.get("epoch"), ds)
            _, r2c = grid_fit(d.get("epochs") or d.get("epoch"), cg)
            print(f"  {Path(f).parts[-2]:<12} dg* 跨度 {sd:.4f} ｜ cg 跨度 {sc:.4f} ｜ "
                  f"比值 {sd/sc:.3f} ｜ dg* R² {r2d:.4f} ｜ cg R² {r2c:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
