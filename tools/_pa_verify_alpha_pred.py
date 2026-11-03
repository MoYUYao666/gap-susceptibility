# -*- coding: utf-8 -*-
r"""复算定理预测 α_pred = -η ∑_m Γ̄_m ‖g_m‖ 与实测 α_obs 的吻合度（#2 溯源）。

## 论文声称（`supplement.tex`）

> "The Theorem prediction --- $\alpha_{\text{pred}} = -\eta\sum_m\bar\Gamma_m\|g_m\|$ --- agrees with the
> empirically fitted $\alpha_{\text{obs}}$ in sign and order of magnitude across all six pilot
> configurations (all negative, within 0.03 of each other), although rank ordering is not preserved at
> this sample size."

**要验证的是**：① 是否全部为负；② |α_pred − α_obs| 是否都 ≤0.03。

## 数据源

`outputs/theory/beta_pilot/*/seed*/beta_results.json` —— 含 `gamma`（Γ、‖g‖、cosφ）、
`alpha_estimated`、`exponential_fit.beta_fitted`。

η（学习率）= 1e-4（`beta_results.json` 的 `learning_rate`）。

    python tools\_pa_verify_alpha_pred.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    rows = []
    for p in sorted(glob.glob(str(REPO / "outputs" / "theory" / "beta_pilot" / "*" / "seed*" / "beta_results.json"))):
        try:
            d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        except Exception:
            continue
        g = d.get("gamma") or {}
        eta = d.get("learning_rate")
        a_obs = d.get("alpha_estimated")
        ne = (g.get("norm_grad_DG_v"), g.get("norm_grad_DG_t"))
        ng = (g.get("norm_g_v"), g.get("norm_g_t"))
        cf = (g.get("cos_phi_v"), g.get("cos_phi_t"))
        if None in (a_obs, eta) or None in ne or None in ng or None in cf:
            continue
        # Γ_m = ‖∇_m DG‖ · cos φ_m ；α_pred = -η Σ_m Γ_m ‖g_m‖
        gamma_v = ne[0] * cf[0]
        gamma_t = ne[1] * cf[1]
        a_pred = -eta * (gamma_v * ng[0] + gamma_t * ng[1])
        cfg = (d.get("config") or {}).get("name", Path(p).parent.parent.name)
        rows.append((cfg, int(d.get("seed", 0)), a_pred, float(a_obs), abs(a_pred - float(a_obs))))

    if not rows:
        print("  ❌ 未找到可复算的记录")
        return 1

    print("=== α_pred vs α_obs 逐条复算（α_pred = -η Σ_m Γ_m ‖g_m‖）===")
    print("  %-24s %-6s %12s %12s %10s" % ("配置", "seed", "α_pred", "α_obs", "|差|"))
    for cfg, seed, ap, ao, d in rows:
        print("  %-24s %-6d %+12.6f %+12.6f %10.6f" % (cfg, seed, ap, ao, d))

    diffs = [r[4] for r in rows]
    neg_p = all(r[2] < 0 for r in rows)
    neg_o = all(r[3] < 0 for r in rows)
    print("\n=== 论文声称核对 ===")
    print("  α_pred 全部为负: %s" % ("✅" if neg_p else "❌"))
    print("  α_obs  全部为负: %s" % ("✅" if neg_o else "❌"))
    print("  |差| 最大 %.6f ｜ 中位 %.6f" % (max(diffs), st.median(diffs)))
    print("  声称『within 0.03』: %s（最大差 %.6f）" % ("✅ 成立" if max(diffs) <= 0.03 else "❌ 不成立", max(diffs)))
    print("  记录数 %d ｜ 论文称 six pilot configurations" % len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
