# -*- coding: utf-8 -*-
r"""A1 摘要收尾压缩：264 → ≤250 词（2026-10-10）。

**只删冗余词，不动任何数字。**

| 原 | 压缩后 | 省 |
|---|---|---|
| "Accuracy rises not from preserving frozen ranks but from \emph{alignment with class structure}: class-conditional contraction improves it" | "Accuracy rises not from preserving frozen ranks but from \emph{class alignment}: contraction toward class centroids improves it" | ~3 |
| "Across the three families assessed---CLIP ViT-B/32, OpenCLIP laion2B, SigLIP base-patch16-224---$\tau$ is the better signal for classification fine-tuning and the gap for retrieval, giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval); we claim this for no other families, benchmarks or mechanisms." | "Across the three families assessed---CLIP ViT-B/32, OpenCLIP laion2B, SigLIP base-patch16-224---$\tau$ is the better classification signal and the gap the better retrieval one, giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval); we claim this for no other families." | ~6 |
| "Across 34 perturbation conditions, three families and seventeen fine-tuned checkpoints (fourteen LoRA, three reconstructed full-fine-tuning), top-1 is governed by $\tau$, not gap magnitude." | "Across 34 perturbation conditions, three families and seventeen fine-tuned checkpoints (fourteen LoRA, three full-fine-tuning), top-1 is governed by $\tau$, not gap magnitude." | ~3 |
| "Under controlled ``gap surgery'' (exact global translations), classification can \emph{collapse while the gap shrinks}" | "Under controlled ``gap surgery'' (exact translations), classification can \emph{collapse while the gap shrinks}" | ~1 |
| "the same both-position LoRA checkpoint measures $\text{CG}\Delta{=}{+}0.033$ on our shared subset and $+0.114$ by the legacy logger; we quote the range, not the larger value." | "the same both-position checkpoint measures $\text{CG}\Delta{=}{+}0.033$ on our subset and $+0.114$ by the legacy logger; we quote the range, not the larger value." | ~3 |

    python tools\_pa_a1_abstract_trim4.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

PAIRS = [
    ("Accuracy rises not from preserving frozen ranks but from \\emph{alignment with class "
     "structure}: class-conditional contraction improves it",
     "Accuracy rises not from preserving frozen ranks but from \\emph{class alignment}: "
     "contraction toward class centroids improves it"),
    ("$\\tau$ is the better signal for classification fine-tuning and the gap for retrieval, "
     "giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval); we claim "
     "this for no other families, benchmarks or mechanisms.",
     "$\\tau$ is the better classification signal and the gap the better retrieval one, "
     "giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval); we claim "
     "this for no other families."),
    ("seventeen fine-tuned checkpoints (fourteen LoRA, three reconstructed full-fine-tuning)",
     "seventeen fine-tuned checkpoints (fourteen LoRA, three full-fine-tuning)"),
    ("Under controlled ``gap surgery'' (exact global translations)",
     "Under controlled ``gap surgery'' (exact translations)"),
    ("the same both-position LoRA checkpoint measures",
     "the same both-position checkpoint measures"),
    ("$\\text{CG}\\Delta{=}{+}0.033$ on our shared subset and",
     "$\\text{CG}\\Delta{=}{+}0.033$ on our subset and"),
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
    print(f"  压缩前：{wc(t)} 词")
    hit = 0
    for old, new in PAIRS:
        c = t.count(old)
        if c == 1:
            t = t.replace(old, new, 1)
            hit += 1
        else:
            print(f"  ⚠ 未命中（{c}）：{old[:50]}…")
    print(f"  命中 {hit}/{len(PAIRS)}")
    after = wc(t)
    print(f"  压缩后：{after} 词{'  ✅ 达标' if after <= 250 else f'  ❌ 超 {after-250}'}")
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("necessary, not sufficient", "self-consistency, not independent validation",
              "no other families", "$r{=}1.000$", "$+0.033$", "$+0.114$",
              "$59.3\\%{\\to}32.0\\%$", "$0.615$", "$0.761$"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ 已压缩；全部数字与保留声明仍在")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
