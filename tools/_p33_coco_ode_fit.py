# -*- coding: utf-8 -*-
r"""为 COCO 补跑数据拟合 ODE（α, β, R²），供替换 `tab:coco_ode`（2026-10-08）。

## 口径（与 `tools/_p1_ledger.py` 完全一致）

拟合对象是 `dg_star`（配对均方距离），网格搜索 β + 解析幅值 A：
`DG*(t) = DG*_0 + (A/β)(1 − e^{−βt})`，`α ≡ A`。

**逐 run 拟合**（不跨 run 池化），再按配置取种子均值±sd。

## 输出

- `outputs/analysis/coco_ode_table.json` —— 表格数据
- 终端打印 LaTeX 行，供直接写入 `supplement.tex`

    python tools\_p33_coco_ode_fit.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "coco_ode_table.json"


def grid_fit(t, y):
    import numpy as np
    t = np.asarray(t, float)
    y = np.asarray(y, float)
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
    # 轨迹文件
    fs = sorted(glob.glob(str(REPO / "outputs/coco_sweep/**/dg_star_history.json"), recursive=True))
    byconf = collections.defaultdict(list)
    for f in fs:
        p = Path(f).parts
        rk, arm, seed = p[-4], p[-3], p[-2]
        d = json.loads(io.open(f, encoding="utf-8").read())
        y = d.get("dg_star")
        if not y or len(y) < 5:
            continue
        A, B, R2 = grid_fit(d["epochs"], y)
        byconf[(arm, rk)].append((seed, A, B, R2))

    print("=== COCO 逐 run ODE 拟合（严格冻结）===")
    print(f"  {'配置':<20} {'seed':<9} {'α':>10} {'β':>9} {'R²':>8}")
    table = []
    for k in sorted(byconf, key=lambda x: (x[0], int(x[1][1:]))):
        arm, rk = k
        rows = byconf[k]
        for seed, A, B, R2 in rows:
            print(f"  {arm + ' r=' + rk[1:]:<20} {seed:<9} {A:>+10.5f} {B:>9.4f} {R2:>8.4f}")
        As = [x[1] for x in rows]; Bs = [x[2] for x in rows]; Rs = [x[3] for x in rows]
        table.append({
            "arm": arm, "rank": int(rk[1:]), "n": len(rows),
            "alpha_mean": st.mean(As), "alpha_sd": st.stdev(As) if len(As) > 1 else None,
            "beta_mean": st.mean(Bs), "beta_sd": st.stdev(Bs) if len(Bs) > 1 else None,
            "r2_mean": st.mean(Rs),
        })
        print(f"  {'  └ 均值':<20} {len(rows)}/3      {st.mean(As):>+10.5f} "
              f"{st.mean(Bs):>9.4f} {st.mean(Rs):>8.4f}")

    print(f"\n  轨迹文件 {len(fs)} 个 ｜ 配置 {len(byconf)} 个")
    missing = [f"{a} r={r[1:]}" for a in ("both", "text_only") for r in ("r1", "r2", "r4", "r16", "r32", "r64")
               if (a, r) not in byconf or len(byconf[(a, r)]) < 3]
    print(f"  未齐 3 seed 的配置: {missing if missing else '无'}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"fits": table, "missing": missing}, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
