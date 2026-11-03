# -*- coding: utf-8 -*-
r"""算清 `dg_pred` vs `dg_actual` 的偏差（供写进 limitation）（2026-10-10）。

## 为什么

`outputs/theory/prospective/prospective_results.json` 里有 6 个 pilot 配置的
**预测 `DG*`（`dg_pred`）** 与 **实际 `DG*`（`dg_actual`）**：

| 配置 | dg_pred | dg_actual |
|---|---|---|
| text_r4 | 0.611 | 1.267 |
| … | … | … |

**肉眼可见两个问题**：① 系统性差约 2.3 倍；② **实测几乎不变**而预测变化大得多。

**本脚本量化**（不靠肉眼）：比值、极差、相关系数、以及"预测的变化是否方向正确"。

    python tools\_p88_dg_pred_bias.py [--apply]
"""
from __future__ import annotations

import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "outputs" / "theory" / "prospective" / "prospective_results.json"
OUT = REPO / "outputs" / "analysis" / "dg_pred_bias.json"


def corr(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


def main() -> int:
    apply = "--apply" in sys.argv
    recs = json.loads(io.open(F, encoding="utf-8").read())
    pred = [r["dg_pred"] for r in recs]
    act = [r["dg_actual"] for r in recs]

    print("=== 逐配置 ===")
    print(f"  {'配置':<12}{'dg_pred':>10}{'dg_actual':>11}{'actual/pred':>13}")
    ratios = []
    for r in recs:
        q = r["dg_actual"] / r["dg_pred"] if r["dg_pred"] else float("nan")
        ratios.append(q)
        print(f"  {r['name']:<12}{r['dg_pred']:>10.4f}{r['dg_actual']:>11.4f}{q:>13.2f}")

    print("\n=== 汇总 ===")
    print(f"  dg_pred   范围 {min(pred):.4f} ~ {max(pred):.4f} ｜ 极差 **{max(pred)-min(pred):.4f}**")
    print(f"  dg_actual 范围 {min(act):.4f} ~ {max(act):.4f} ｜ 极差 **{max(act)-min(act):.4f}**")
    print(f"  极差之比（预测/实测）= **{(max(pred)-min(pred))/max(max(act)-min(act),1e-12):.2f}×**")
    print(f"  actual/pred 中位比 = **{st.median(ratios):.2f}×**（系统性偏低）")
    print(f"  corr(dg_pred, dg_actual) = **{corr(pred, act):+.4f}**")

    print("\n=== 关键：预测的**变化方向**是否正确 ===")
    # 以 text_r4 为基准比较各配置的"变化量"
    base_p = pred[0]
    base_a = act[0]
    ok = 0
    for r in recs[1:]:
        dp = r["dg_pred"] - base_p
        da = r["dg_actual"] - base_a
        same = (dp * da) > 0
        ok += same
        print(f"  {r['name']:<12} Δpred={dp:+.4f} ｜ Δactual={da:+.4f} ｜ "
              f"{'✅ 同向' if same else '❌ 反向'}")
    print(f"  → 方向一致 {ok}/{len(recs)-1}")

    verdict = {
        "systematic_ratio_median": st.median(ratios),
        "pred_spread": max(pred) - min(pred),
        "actual_spread": max(act) - min(act),
        "spread_ratio": (max(pred) - min(pred)) / max(max(act) - min(act), 1e-12),
        "corr": corr(pred, act),
        "direction_agreement": f"{ok}/{len(recs)-1}",
    }
    print("\n=== 结论 ===")
    print("  ① **系统性偏低**：实测 / 预测 中位比 ≈ %.2f×" % verdict["systematic_ratio_median"])
    print("  ② **变化幅度被高估 %.2f 倍**：预测极差 %.3f vs 实测极差 %.3f"
          % (verdict["spread_ratio"], verdict["pred_spread"], verdict["actual_spread"]))
    print("  ③ 相关性 %+.4f" % verdict["corr"])
    print("  ④ 变化方向一致 %s" % verdict["direction_agreement"])

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"rows": recs, "verdict": verdict}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
