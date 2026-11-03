# -*- coding: utf-8 -*-
r"""把摘要压到 ≤250 词（第二轮）（2026-10-13）。

## 现状

`_p486` 得 **291 词**（上限 250）⇒ 还需砍约 50 词。

**砍法**：五项要求**只列关键词**（完整列表在正文 R1–R5）；删去可由正文承载的解释性从句；
保留**全部实质结论**（含对我方不利的三条）与**定位句**。

    python tools\_p487_trim_abstract2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper3" / "paper_ieee" / "main.tex"

START = "We study how to allocate PEFT rank across the blocks"
END = "not allocating better than a search."

NEW = (
    r"We study how to allocate PEFT rank across the blocks of a multimodal model when the"
    "\n"
    r"target cannot be searched, so the decision must come from the source model alone. The"
    "\n"
    r"central object is the cross-modal gradient coupling"
    "\n"
    r"$\Gamma_k=\langle\nabla_{M_k}E,u_{M_k}\rangle$. Asking what an admissible allocation"
    "\n"
    r"statistic can be, we show that under five requirements---pre-training computability,"
    "\n"
    r"invariance under block-wise orthogonal reparameterisation, block decomposability, sign"
    "\n"
    r"consistency with alignment, and first-order observability---a statistic must be additive in"
    "\n"
    r"the per-block contributions, and that this additivity is an assumption, not a consequence:"
    "\n"
    r"block decomposability alone does not imply it, as $\|\nabla E\|^2$ shows. Stated"
    "\n"
    r"explicitly, it makes $\Gamma$ unique up to positive scaling, and constrained optimisation"
    "\n"
    r"gives $\mathrm{rank}_k\propto\exp(-\beta|\Gamma_k|)$."
    "\n\n"
    r"$\Gamma$ measured on CLIP predicts a rank allocation for LLaVA instruction tuning with no"
    "\n"
    r"target-model gradient. At an identical trainable-parameter count the $\Gamma$-guided"
    "\n"
    r"allocation beats the uniform-rank baseline at one learning rate, but the advantage reverses"
    "\n"
    r"at another and vanishes once the arms are matched on training loss; we therefore report a"
    "\n"
    r"zero-shot heuristic, not an optimum. Three controls bound its scope: it is indistinguishable"
    "\n"
    r"from a random allocation of the same budget; AdaLoRA, swept over the same rates, reaches"
    "\n"
    r"lower alignment energy than any of our arms; and the critical rank we had bracketed at"
    "\n"
    r"$r_c\in[5,6]$ belongs to the protocol, not to the model. That protocol is the largest"
    "\n"
    r"caveat: its visual inputs are blank images, and at the paper's operating point a blank image"
    "\n"
    r"carries three times the initialization alignment energy of a real one, so the objective"
    "\n"
    r"optimised is not the one a real input induces. We close by delimiting the rule's purpose:"
    "\n"
    r"allocating without searching."
    "\n")


def count_words(s: str) -> int:
    return len(re.sub(r"\\[a-zA-Z]+|[{}$\\]", " ", s).split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()
    i = t.find(START)
    j = t.find(END, i)
    if i < 0 or j < 0:
        print(f"  🔴 锚点未命中（i={i}, j={j}）")
        return 1
    end = j + len(END)
    print(f"  旧 {count_words(t[i:end])} 词 → 新 {count_words(NEW)} 词（上限 250）")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = MAIN.with_suffix(".tex.bak_p487")
    if not bak.exists():
        shutil.copy2(MAIN, bak)
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t[:i] + NEW + t[end:])
    t2 = io.open(MAIN, encoding="utf-8", errors="replace").read()
    ab = t2[t2.find("\\begin{abstract}"):t2.find("\\noindent\\textbf{Keywords")]
    w = count_words(ab)
    print(f"  → 摘要粗估 {w} 词 {'✅ ≤250' if w <= 250 else '🔴 超标'}")
    checks = {
        "≤250 词": w <= 250,
        "删掉 30×": "$30\\times$" not in ab,
        "unique 需额外假设": "an assumption, not a consequence" in ab,
        "含反例": "$\\|\\nabla E\\|^2$" in ab,
        "r_c 归属协议": "belongs to the protocol" in ab,
        "含 loss 匹配": "matched on training loss" in ab,
        "含与随机不可区分": "indistinguishable" in ab,
        "含 AdaLoRA": "AdaLoRA" in ab,
        "含 blank 3×": "three times the initialization" in ab,
        "含定位句": "allocating without searching" in ab,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
