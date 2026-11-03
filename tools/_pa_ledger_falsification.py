# -*- coding: utf-8 -*-
r"""把两处否证的数字加进门禁台账（2026-10-10）。

新增数字：
- `f(DG₀) = +66.7 ± 4.8`（`alpha_precision.json`）
- 归档 `α_fit = −2.7743e−3` → `f_fit = −27.7`
- 三位置 `f` 极差 1.4%
- 驱动项轨迹均值 `+10.8 / +9.2 / +10.2`，极差 `16.5%`
- 实测 CGΔ 极差 `277%`

    python tools\_pa_ledger_falsification.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

ANCHOR = "    # ── ①d dg_pred 偏差"

ADD = '''    # ── ①e 两处理论否证（2026-10-10 加入 discussion 的 Seventh / Eighth）──
    ap = json.loads(io.open(REPO / "outputs/analysis/alpha_precision.json",
                            encoding="utf-8").read())
    claim("f(DG0) 高精度合并值", 66.7, ap["pooled_f"]["mean"],
          "alpha_precision.json:pooled_f.mean", tol=0.2)
    claim("f(DG0) 标准误", 4.8, ap["pooled_f"]["se"],
          "alpha_precision.json:pooled_f.se", tol=0.1)
    claim("归档 alpha_fit", -2.7743e-3, ap["alpha_fit_archive"],
          "alpha_precision.json:alpha_fit_archive", tol=1e-6)
    claim("f_fit = alpha_fit/eta", -27.7, ap["f_fit_archive"],
          "alpha_precision.json:f_fit_archive", tol=0.1)
    dt = json.loads(io.open(REPO / "outputs/analysis/driving_trajectory.json",
                            encoding="utf-8").read())
    for _a, _paper in (("text_only", 10.8), ("vision_only", 10.2), ("both", 9.2)):
        claim(f"驱动项轨迹均值 {_a}", _paper, dt["trajectory_means"][_a],
              f"driving_trajectory.json:trajectory_means.{_a}", tol=0.1)
    claim("驱动项极差(%)", 16.5, dt["trajectory_mean_spread_pct"],
          "driving_trajectory.json:trajectory_mean_spread_pct", tol=0.2)
    _dv = json.loads(io.open(REPO / "outputs/analysis/driving_verdict.json",
                             encoding="utf-8").read())
    claim("实测 CGΔ 极差(%)", 277.0, _dv["cg_delta_spread_pct"],
          "driving_verdict.json:cg_delta_spread_pct", tol=2.0)

''' + ANCHOR


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "两处理论否证（2026-10-10" in t:
        print("  已加，跳过")
        return 0
    if t.count(ANCHOR) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(ANCHOR)}）")
        return 1
    t = t.replace(ANCHOR, ADD, 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 已加 8 条主张（f(DG0)/se/alpha_fit/f_fit/三个轨迹均值/极差×2）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
