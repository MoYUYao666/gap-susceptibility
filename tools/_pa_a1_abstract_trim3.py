# -*- coding: utf-8 -*-
r"""A1 摘要终压：标准口径 287 → ≤250 词（2026-10-10）。

**原则：删掉"复述性"短语，保住每一个数字与保留声明。**

| 原 | 压缩后 | 省 |
|---|---|---|
| "Fine-tuning a contrastive vision--language model for classification moves the modality gap and erodes class-relative rank order at the same time. Only the second governs zero-shot accuracy, and it can be monitored at no extra cost: the Kendall order-preservation coefficient $\tau$ is computed from the top-$k$ class sets a validation pass already produces." | "Classification fine-tuning of a contrastive vision--language model moves the modality gap and erodes class-relative rank order together. Only the second governs zero-shot accuracy, and it is free to monitor: the Kendall order-preservation coefficient $\tau$ follows from the top-$k$ class sets a validation pass already produces." | ~10 |
| "The modality gap is therefore not a universal health metric---narrowing it is an explicit objective and gap-based quantities predict retrieval degradation, but that reading does not extend to zero-shot classification." | "The modality gap is therefore no universal health metric: gap-based quantities predict retrieval degradation, but that reading does not extend to zero-shot classification." | ~8 |
| "while real fine-tuning can grow the gap with no zero-shot loss" | "while real fine-tuning can grow the gap without zero-shot loss" | 1 |
| "Across 34 perturbation conditions, three families and seventeen fine-tuned checkpoints ($\dots$), zero-shot top-1 is governed by the Kendall order-preservation coefficient $\tau$ of class-relative similarity ranks, not gap magnitude." | "Across 34 perturbation conditions, three families and seventeen fine-tuned checkpoints ($\dots$) top-1 is governed by $\tau$, not gap magnitude." | ~10 |
| "Across the three families assessed---CLIP ViT-B/32, OpenCLIP laion2B, SigLIP base-patch16-224---$\tau$ is the better signal for classification fine-tuning and the gap for retrieval, giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval); we claim this for no other families, benchmarks or mechanisms." | "Across the three families assessed---CLIP ViT-B/32, OpenCLIP laion2B, SigLIP base-patch16-224---$\tau$ is the better signal for classification and the gap for retrieval, giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval); we claim this for no other families, benchmarks or mechanisms." | ~2 |

    python tools\_pa_a1_abstract_trim3.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

PAIRS = [
    ("Fine-tuning a contrastive vision--language model for classification moves the "
     "modality gap and erodes class-relative rank order at the same time. Only the second "
     "governs zero-shot accuracy, and it can be monitored at no extra cost: the Kendall "
     "order-preservation coefficient $\\tau$ is computed from the top-$k$ class sets a "
     "validation pass already produces. The modality gap is therefore not a universal "
     "health metric---narrowing it is an explicit objective and gap-based quantities "
     "predict retrieval degradation, but that reading does not extend to zero-shot "
     "classification.",
     "Classification fine-tuning of a contrastive vision--language model moves the "
     "modality gap and erodes class-relative rank order together. Only the second governs "
     "zero-shot accuracy, and it is free to monitor: the Kendall order-preservation "
     "coefficient $\\tau$ follows from the top-$k$ class sets a validation pass already "
     "produces. The modality gap is therefore no universal health metric: gap-based "
     "quantities predict retrieval degradation, but that reading does not extend to "
     "zero-shot classification."),
    ("while real fine-tuning can \\emph{grow the gap} with no zero-shot loss",
     "while real fine-tuning can \\emph{grow the gap} without zero-shot loss"),
    ("zero-shot top-1 is governed by the Kendall order-preservation coefficient $\\tau$ of "
     "class-relative similarity ranks, not gap magnitude.",
     "top-1 is governed by $\\tau$, not gap magnitude."),
    ("$\\tau$ is the better monitoring signal for classification-oriented fine-tuning, the "
     "gap for retrieval",
     "$\\tau$ is the better signal for classification and the gap for retrieval"),
]


def wc(t: str) -> int:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if not m:
        return -1
    b = re.sub(r"\\[a-zA-Z]+", " ", m.group(1))
    b = re.sub(r"[{}$\\]", " ", b)
    return len(b.split())


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    print(f"  压缩前（标准口径）：{wc(t)} 词")
    for old, new in PAIRS:
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠'} 命中 {c}: {old[:56]}…")
        if c == 1:
            t = t.replace(old, new, 1)
    after = wc(t)
    print(f"  压缩后：{after} 词（限 250）{'  ✅ 达标' if after <= 250 else f'  ❌ 超 {after-250}'}")
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("necessary, not sufficient", "self-consistency, not independent validation",
              "no other families", "$r{=}1.000$", "$+0.033$", "$+0.114$",
              "$59.3\\%{\\to}32.0\\%$", "$0.615$", "$0.761$", "$59.3\\%{\\to}78.6\\%$"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ 已压缩；全部数字与保留声明仍在")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
