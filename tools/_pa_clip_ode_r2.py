# -*- coding: utf-8 -*-
r"""统计 CLIP 侧 ODE 拟合的 R² 分布（`exponential_fit.r_squared`），核验"mean R² > 0.96"。

## 为什么先前查错

`tools/_pa_verify_core_claims.py` 与 `tools/_pa_r2_distribution.py` 按键名 `R2/r2/R^2` 搜索，
**漏掉了 `r_squared`** —— 而 CLIP 侧 ODE 拟合的 R² 正是存在这个键名下
（`outputs/theory/**/beta_results.json` → `exponential_fit.r_squared`）。

先前看到的 13 处 R² 全部来自 `llava_*`（**解码器**实验），与"162 个 CLIP 拟合"的主张无关。

## 本脚本输出

1. 所有 `beta_results.json` 的 `r_squared` 分布（min/p25/median/mean/max）；
2. 按配置归组（rank / 位置 / full_ft）；
3. 与正文"mean R² > 0.96"和"162 fits"对照，结论是否成立。

    python tools\_pa_clip_ode_r2.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    rows: list[tuple[str, float]] = []
    for p in sorted(glob.glob(str(REPO / "outputs" / "**" / "beta_results.json"), recursive=True)):
        try:
            d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        except Exception:
            continue
        r2 = (d.get("exponential_fit") or {}).get("r_squared")
        if isinstance(r2, (int, float)):
            cfg = (d.get("config") or {}).get("name") or Path(p).parent.parent.name
            rows.append((cfg, float(r2)))

    if not rows:
        print("  未找到 beta_results.json 的 r_squared")
        return 1

    vals = sorted(x[1] for x in rows)
    print(f"=== CLIP 侧 ODE 拟合 R²（{len(vals)} 条，来源 outputs/**/beta_results.json）===")
    print(f"  min {vals[0]:.4f} ｜ p25 {vals[len(vals)//4]:.4f} ｜ median {st.median(vals):.4f}"
          f" ｜ mean {st.mean(vals):.4f} ｜ max {vals[-1]:.4f}")
    print(f"  ≥0.96: {sum(1 for v in vals if v >= 0.96)}/{len(vals)}"
          f" ｜ mean > 0.96: {'✅ 成立' if st.mean(vals) > 0.96 else '❌ 不成立'}")
    print(f"  最低 5 条: {['%.4f' % v for v in vals[:5]]}")

    print("\n=== 按配置归组（均值）===")
    g: dict[str, list[float]] = defaultdict(list)
    for cfg, r2 in rows:
        g[cfg].append(r2)
    for cfg in sorted(g, key=lambda k: st.mean(g[k])):
        v = g[cfg]
        print(f"  {cfg:34s} n={len(v):3d}  mean {st.mean(v):.4f}  min {min(v):.4f}  max {max(v):.4f}")

    print("\n=== 与正文主张对照 ===")
    print(f"  正文: 'predicts the full gap trajectory with mean $R^2 > 0.96$ across all tested LoRA configurations'")
    print(f"  实测: mean = {st.mean(vals):.4f} ｜ median = {st.median(vals):.4f}")
    print(f"  正文: '162 additional experiments' ｜ 实测记录数 = {len(vals)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
