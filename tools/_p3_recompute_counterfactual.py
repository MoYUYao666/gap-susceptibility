# -*- coding: utf-8 -*-
"""独立重算 P3 反事实批的 ΔE 统计，对照稿件与封面信里引用的数字。

口径说明（关键）：
  稿件写 "mean ± sample std over 5 seeds"、"sample std over 13 valid runs"，
  故应以 **样本标准差（ddof=1）** 对照；本脚本同时给出总体 sd 以便区分。

    python tools/_p3_recompute_counterfactual.py
"""
from __future__ import annotations

import json
import math
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper3" / "scripts" / "outputs" / "experiments" / "all_results.json"

# 稿件/封面信引用的数字（experiments.tex:270-279）
CLAIMS = {
    "Theory": (-108.0, 27.0, 5),
    "Random": (491.0, 808.0, 13),
    "Violation_r16": (1507.8, 155.0, 5),
    "Violation_r32": (None, None, 5),   # 5/5 NaN
}


def sd(vals: list[float], ddof: int) -> float:
    if len(vals) <= ddof:
        return float("nan")
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - ddof))


def delta_e(run: dict) -> float | None:
    """从一次运行里取 ΔE（post - init）；缺失或 NaN 记 None。"""
    for k in ("dE", "delta_E", "deltaE"):
        if k in run and isinstance(run[k], (int, float)):
            v = float(run[k])
            return None if math.isnan(v) else v
    # 由 E 序列推：末值 - 首值
    e = run.get("E")
    if isinstance(e, list) and len(e) >= 2 and all(isinstance(x, (int, float)) for x in e):
        v = float(e[-1]) - float(e[0])
        return None if math.isnan(v) else v
    # 由 E0 / E_final 推
    if isinstance(run.get("E0"), (int, float)) and isinstance(run.get("E_final"), (int, float)):
        v = float(run["E_final"]) - float(run["E0"])
        return None if math.isnan(v) else v
    return None


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    print(f"源档案: {SRC.relative_to(REPO)}")
    print(f"顶层条件: {list(data.keys())}\n")

    # 打印一次运行的结构，便于核对抽取逻辑
    first = next(iter(data.values()))
    if isinstance(first, list) and first:
        print("单次运行的键:", sorted(first[0].keys())[:15], "\n")

    print(f"{'条件':<16}{'有效n':>6}{'NaN':>5}{'mean':>10}{'sd(样本)':>11}{'sd(总体)':>11}   稿件值")
    print("-" * 78)
    for cond, runs in data.items():
        if not isinstance(runs, list):
            continue
        vals, nans = [], 0
        for r in runs:
            v = delta_e(r) if isinstance(r, dict) else None
            if v is None:
                nans += 1
            else:
                vals.append(v)
        if vals:
            mean, s1, s0 = st.mean(vals), sd(vals, 1), sd(vals, 0)
            row = f"{cond:<16}{len(vals):>6}{nans:>5}{mean:>10.1f}{s1:>11.1f}{s0:>11.1f}"
        else:
            row = f"{cond:<16}{0:>6}{nans:>5}{'—':>10}{'—':>11}{'—':>11}"
        cl = CLAIMS.get(cond)
        if cl and cl[0] is not None:
            row += f"   {cl[0]:+.1f} ± {cl[1]:.0f} (n={cl[2]})"
        elif cl:
            row += f"   全 {cl[2]} 次 NaN"
        print(row)

    # 专项：封面信的 "30× larger standard deviation (808 vs 27)"
    print("\n--- 封面信的关键断言：Random 的 sd 是 Theory 的 30× ---")
    th = [delta_e(r) for r in data.get("Theory", [])]
    rd = [delta_e(r) for r in data.get("Random", [])]
    th_v = [v for v in th if v is not None]
    rd_v = [v for v in rd if v is not None]
    if th_v and rd_v:
        s_th, s_rd = sd(th_v, 1), sd(rd_v, 1)
        print(f"  Theory: n={len(th_v)} sd={s_th:.1f}")
        print(f"  Random: n={len(rd_v)} sd={s_rd:.1f}（另有 {len(rd)-len(rd_v)} 次 NaN）")
        print(f"  比值: {s_rd / s_th:.1f}×   稿件写 30×，并用 (808 vs 27)")
        print(f"  四舍五入后: {round(s_rd):.0f} vs {round(s_th):.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
