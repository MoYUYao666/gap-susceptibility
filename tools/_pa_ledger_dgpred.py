# -*- coding: utf-8 -*-
r"""把 limitation 的 `dg_pred` 数字加进门禁台账（2026-10-10）。

## 为什么

论文新增了 5 个数字（`discussion.tex` 的 Sixth）：
- 中位比 **2.44×**
- 极差比 **3.33×**（`0.223` vs `0.067`）
- 相关 **+0.225**
- 方向一致 **2/5**
- `α` 的中位相对误差 **34%**

**唯一原则：每个数字必须指名来源。**

    python tools\_pa_ledger_dgpred.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

ANCHOR = "    # ── ①c 解码器 VLM（实验 ④"

ADD = '''    # ── ①d dg_pred 偏差（2026-10-10 加入 discussion 的 Sixth limitation）──
    dp = json.loads(io.open(REPO / "outputs/analysis/dg_pred_bias.json",
                            encoding="utf-8").read())["verdict"]
    claim("dg_pred 实测/预测中位比", 2.44, dp["systematic_ratio_median"],
          "dg_pred_bias.json:verdict.systematic_ratio_median", tol=0.02)
    claim("dg_pred 极差比(预测/实测)", 3.33, dp["spread_ratio"],
          "dg_pred_bias.json:verdict.spread_ratio", tol=0.02)
    claim("dg_pred 预测极差", 0.223, dp["pred_spread"],
          "dg_pred_bias.json:verdict.pred_spread", tol=0.002)
    claim("dg_pred 实测极差", 0.067, dp["actual_spread"],
          "dg_pred_bias.json:verdict.actual_spread", tol=0.002)
    claim("dg_pred 相关系数", 0.225, dp["corr"],
          "dg_pred_bias.json:verdict.corr", tol=0.01)
    pr = json.loads(io.open(REPO / "outputs/theory/prospective/prospective_results.json",
                            encoding="utf-8").read())
    import statistics as _st
    _rels = [abs((r["alpha_pred"] - r["alpha_actual"]) / r["alpha_actual"]) for r in pr]
    claim("alpha 预测中位相对误差(%)", 34.0, _st.median(_rels) * 100,
          "prospective_results.json:median rel err of alpha_pred", tol=1.0)

''' + ANCHOR


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "dg_pred 偏差（2026-10-10" in t:
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
    print("  ✅ 已加 6 条主张（2.44 / 3.33 / 0.223 / 0.067 / 0.225 / 34%）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
