# -*- coding: utf-8 -*-
r"""把摘要压到 PRL 上限（250 词）以内（2026-10-13）。

## 现状

我 `_p485` 写的摘要 **334 词**（粗估 339），**PRL 要求 ≤250 词**（Guide：*"a concise and factual
abstract that does not exceed 250 words"*）⇒ **必须再压约 90 词**。

**原则**：保留全部**已核实的实质结论**（含对我方不利的三条），压缩的是**措辞而非内容**。

    python tools\_p486_trim_abstract.py [--apply]
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
    r"central object is the cross-modal gradient coupling coefficient"
    "\n"
    r"$\Gamma_k=\langle\nabla_{M_k}E,u_{M_k}\rangle$. We ask what an admissible allocation"
    "\n"
    r"statistic can be, and show that under five requirements---pre-training computability,"
    "\n"
    r"invariance under block-wise orthogonal reparameterisation, block decomposability, sign"
    "\n"
    r"consistency with alignment, and first-order observability---a statistic must be additive in"
    "\n"
    r"the per-block contributions, and that this is an additional assumption, not a consequence:"
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
    r"at another and vanishes once the arms are matched on training loss, so we report a zero-shot"
    "\n"
    r"heuristic, not an optimum. Three controls bound the scope: the rule is indistinguishable"
    "\n"
    r"from a random allocation of the same budget; AdaLoRA, swept over the same rates, reaches"
    "\n"
    r"lower alignment energy than any of our arms; and the critical rank we had bracketed at"
    "\n"
    r"$r_c\in[5,6]$ belongs to the protocol, not to the model. That protocol is the largest"
    "\n"
    r"caveat: its visual inputs are blank images, and at the paper's own operating point a blank"
    "\n"
    r"image carries three times the initialization alignment energy of a real one, so the"
    "\n"
    r"objective optimised is not the one a real input induces. We close by delimiting the rule's"
    "\n"
    r"purpose: allocating without searching, not allocating better than a search."
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
    old = t[i:end]
    print(f"  旧 {count_words(old)} 词 → 新 {count_words(NEW)} 词（上限 250）")
    if count_words(NEW) > 250:
        print(f"  🔴 仍超上限")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = MAIN.with_suffix(".tex.bak_p486")
    if not bak.exists():
        shutil.copy2(MAIN, bak)
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t[:i] + NEW + t[end:])
    t2 = io.open(MAIN, encoding="utf-8", errors="replace").read()
    ab = t2[t2.find("\\begin{abstract}"):t2.find("\\noindent\\textbf{Keywords")]
    w = count_words(ab)
    print(f"  ✅ 已写；摘要全文粗估 {w} 词 {'✅ ≤250' if w <= 250 else '🔴 超标'}")
    checks = {
        "≤250 词": w <= 250,
        "删掉 30×": "$30\\times$" not in ab,
        "unique 已限定为'额外假设'": "additional assumption" in ab,
        "含反例": "$\\|\\nabla E\\|^2$" in ab,
        "r_c 归属协议": "belongs to the protocol" in ab,
        "含容量匹配与 loss 匹配": "matched on training loss" in ab,
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
