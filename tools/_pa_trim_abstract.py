# -*- coding: utf-8 -*-
r"""把 Paper A 摘要压回 250 词以内（改写后曾达 376 词）。

## 为什么必须压

Elsevier 各刊摘要上限常见为 **250 词**（Neurocomputing 等）。
目标刊尚未最终确定，但 376 词对任何 Elsevier 刊都超限，属可预见的退修点。

## 压法

保留：问题、Γ 的推导、ODE 及 R²、三条后果（含**架构依赖**这一新结论）、验证规模与严格冻结对照。
删减：重复措辞、可省的限定语、把 $\beta$ 的批次差异细节并入一句。

    python tools\_pa_trim_abstract.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "main_springer.tex"

NEW_ABS = r"""\abstract{
Fine-tuning a vision-language model on a small corpus often widens the gap between its image and text
embeddings. We first characterise when that happens: across $n=204$ archived experiments the Distribution
Gap predicts retrieval degradation ($r=-0.71$) more strongly than the Centroid Gap ($r=-0.59$), and which
part of the model is adapted matters more than how its adapters are configured.

We then derive \emph{Gap Susceptibility} $\Gamma_m = \|\nabla_m DG^*\| \cdot \cos\phi_m$ from gradient
flow: with the alignment energy $DG^*$ as a state variable, the rate of gap change is the projection of
the task gradient onto the alignment gradient, so $\Gamma_m$ splits into sensitivity and
directional-coupling terms.

This yields a first-order ODE $d(DG^*)/dt = \alpha - \beta(DG^*-DG_0)$, with
$\alpha = -\eta\sum_m \bar{\Gamma}_m\|g_m\|$ the perturbation force (Theorem~\ref{thm:ode}) and $\beta$
the restoring coefficient. The ODE predicts the full gap trajectory at mean $R^2 > 0.96$ across all
tested LoRA configurations, against $R^2 = 0.00$ for a constant baseline and $0.946$ for a linear one.
$\beta$ is stable within PEFT ($\mathrm{CV}=13.3\%$), whereas its full-fine-tuning estimate varies with
batch ($0.159$ against $0.643$).

Three consequences follow: adaptation position, with $g_v=0$ removing the dominant perturbation source
when only the text side is trained; a protective bound for LoRA ($\alpha<0$ across ranks); and a task
gradient whose effective dimension is set by task structure rather than configured rank, leaving
$\|g_v\|$ flat across ranks ($k=0.043$). Validation spans 278 experiments over five architectures, three
PEFT methods and two retrieval datasets. A strict-freezing control training only adapter matrices
confirms the predicted ordering on CLIP and reverses it on SigLIP: the text-only advantage is a property
of the architecture, not a universal default.
}"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    m = re.search(r"\\abstract\{[\s\S]*?\n\}", t)
    if not m:
        print("  ⚠ 未找到 \\abstract{...}")
        return 1
    old = m.group(0)

    def wc(s: str) -> int:
        body = re.search(r"\\abstract\{([\s\S]*?)\n\}", s).group(1)
        plain = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?", " ", body)
        plain = re.sub(r"[$\\{}]", "", plain)
        return len(plain.split())

    print("  旧摘要 %d 词 → 新摘要 %d 词" % (wc(old), wc(NEW_ABS)))
    if wc(NEW_ABS) > 250:
        print("  ⚠ 仍超 250 词，请再压")
        return 1
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(old, NEW_ABS, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "-0.827" not in t2 and "companion empirical study" not in t2
        assert "architecture, not a universal default" in t2
        print("  ✅ 已写入并断言通过（旧值/循环引用仍在清除状态，架构依赖保留）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
