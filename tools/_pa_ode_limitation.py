# -*- coding: utf-8 -*-
r"""在 discussion 的 Limitations 中补入**拟合口径**与**归档差额**的如实说明（2026-10-07）。

## 为什么必须补

按操作者决定（B）改完数字后，**只改数字不说明原因**是不可接受的——读者/审稿人会问
"R² 为何从 0.986 变成 0.949"。**必须如实写清两件事**：

1. **拟合口径**：$\alpha$、$\beta$ 是**逐 run 拟合**的（不是从梯度算出的预测）；
2. **归档与执行的差额**：正文原先声称 162 runs，`outputs/` 中可复核 55 条 LoRA run
   → **如实披露**，并说明这限制了可复现范围。

**同时**：把"预测"一词的用法收窄（拟合口径下不宜称"predicts trajectories"）。

    python tools\_pa_ode_limitation.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

OLD_TAIL = ("Second, our study is limited to contrastive dual-encoder architectures; whether the framework "
            "generalizes to decoder-based VLMs or generation-oriented objectives remains open. Third, the ODE "
            "derivation uses $DG^*$ as a differentiable proxy for the Distribution Gap; their close agreement "
            "in the pilot runs supports the substitution, but formal bounds on the approximation error are not "
            "yet established.")

NEW_TAIL = OLD_TAIL + (" Fourth, the fit accuracies reported in Section~\\ref{sec:validation} are obtained "
                       "with $\\alpha$ and $\\beta$ fitted to each trajectory, not predicted from its gradients. "
                       "The gradient-flow identity itself is verified directly rather than through the fit "
                       "(Section~\\ref{sec:theory}), but the coefficient values entering the trajectories are "
                       "estimated from the data they describe, so the fit accuracies measure whether the "
                       "functional form is adequate rather than whether the coefficients are computable in "
                       "advance. Fifth, the trajectories analysed here are a subset of those originally "
                       "produced for the rank sweep: $55$ LoRA runs are archived and reproducible "
                       "($43$ on Flickr30k, $6$ on MS-COCO) at three seeds per configuration, against the "
                       "larger set of runs the sweep originally comprised at five seeds. Everything reported "
                       "in Section~\\ref{sec:validation} is computed from the archived runs and is reproducible "
                       "from them; the figures quoted should be read as properties of that archived set.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "Fourth, the fit accuracies reported" in t:
        print("  已补入，跳过")
        return 0
    c = t.count(OLD_TAIL)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中 Limitations 段尾")
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD_TAIL, NEW_TAIL, 1))
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("fitted to each trajectory, not predicted from its gradients",
              "subset of those originally produced", "$55$ LoRA runs are archived",
              "read as properties of that archived set"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ 已补入并断言通过（{len(t2.splitlines())} 行）")

    # 摘要/引言里"predicts"的用法收窄（拟合口径下不宜称 predicts trajectories）
    MAIN = REPO / "paper合" / "main_nc.tex"
    m = io.open(MAIN, encoding="utf-8").read()
    old_main = "The ODE\npredicts the full gap trajectory at mean $R^2 = 0.949$ across the tested LoRA configurations"
    new_main = ("The ODE\nreproduces the full gap trajectory at mean $R^2 = 0.949$ across the tested LoRA configurations")
    if old_main in m:
        io.open(MAIN, "w", encoding="utf-8", newline="").write(m.replace(old_main, new_main, 1))
        print("  ✅ 摘要：'predicts' → 'reproduces'（拟合口径下更准确）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
