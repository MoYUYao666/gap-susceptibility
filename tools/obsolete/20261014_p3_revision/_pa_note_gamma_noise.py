# -*- coding: utf-8 -*-
r"""A：在论文里补"`Γ_m` 的朴素逐批估计噪声极大"这一**实用性事实**（2026-10-10）。

## 为什么只补一句，而不删"可预测"的措辞

**核对原文后发现**（`theory.tex` / `supplement.tex`）：
- **恒等式验证**是**配对**测量（`−η⟨∇DG*,∇L⟩` vs **真实 optimizer step 的变化**），
  corr **0.998**、中位误差 **2.7%** → **成立**；
- **α 预测**只声称"**同号、同量级**"，并**明说"rank ordering is not preserved at this sample size"**；
- **β 的闭式预测**已标注"**40× smaller**…left to future work"。

**→ 原文比我的批评更严谨。** 我的批评针对的是"**平均梯度对平均梯度**"的估计
（`_p79`/`_p81` 的做法），而那**不是原文验证恒等式的方式**。

**但有一个实用事实原文没写**，值得补：**朴素的逐批估计噪声极大**
（`sd 27–49` vs `mean 18–32`）→ **要用配对测量，不要用朴素平均**。

## 改动

在 `supplement.tex` C 节 `α` 预测段落后**追加一段**，写明该 Monte Carlo 噪声实测值。

    python tools\_pa_note_gamma_noise.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD = (r"although rank ordering is not preserved at this sample size.")

NEW = (r"""although rank ordering is not preserved at this sample size. The variance of
this estimator is worth recording, because it is large and it dictates how
$\Gamma_m$ must be measured in practice. Estimates of
$\sum_m\langle\nabla_m DG^*,g_m\rangle$ formed from a single batch of $64$ or $128$
pairs spread over roughly $-86$ to $+72$ with a standard deviation of $27$--$49$,
against a mean of $18$--$32$, so a batch-level estimate carries a signal-to-noise
ratio near unity and its sign is not stable. The consequence is that $\Gamma_m$
should be estimated by \emph{paired} measurement---forming the predicted step
$-\eta\langle\nabla_\theta DG^*,\nabla_\theta\mathcal{L}\rangle$ and comparing it
to the change an actual optimiser step produces at the same state, as done above,
where the correlation reaches $0.998$---rather than by averaging independent
batch-level estimates, which requires of order $10^2$--$10^3$ batches to reach
$10\%$ relative precision. We report this because it bounds how the framework can
be used: the ODE's coefficients are obtained by fitting each trajectory, which is
deterministic, and the gradient-level quantities above are diagnostic of the
mechanism rather than a practical route to predicting $\alpha$ and $\beta$ in
advance.""")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "signal-to-noise" in t and "paired" in t and "worth recording" in t:
        print("  已补，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD)}）")
        return 1
    t = t.replace(OLD, NEW, 1)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("signal-to-noise", "paired", "10^2$--$10^3", "deterministic",
              "rather than a practical route"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ supplement.tex 已补：Monte Carlo 噪声实测 + 建议用配对测量")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
