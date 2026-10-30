# -*- coding: utf-8 -*-
r"""把摘要压到 ≤250 词（第三轮，最终）（2026-10-13）。

## 三轮压缩记录（可追溯）

| 轮 | 词数 | 做了什么 |
|---|---|---|
| `_p485` 首写 | **334** | 清掉"30×"等与正文矛盾的主张 + 写入三条对我方不利的结论 |
| `_p486` | **291** | 压措辞 |
| `_p487` | **281** | 五项要求只留关键词 |
| **本脚本** | 目标 **≤250** | 删去可移入正文的解释性从句；**不动任何实质结论** |

**必须保留的三条不利结论**（这是本轮修订的核心价值）：
① 优势随 lr 反转 / 匹配 loss 后消失；② 与同预算随机不可区分；③ AdaLoRA 更优；④ $r_c$ 属协议；⑤ blank 非中性（3×）。

    python tools\_p488_trim_abstract3.py [--apply]
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
END = "allocating without searching."

NEW = (
    r"We allocate PEFT rank across the blocks of a multimodal model when the target cannot be"
    "\n"
    r"searched, so the decision must come from the source model alone. The central object is the"
    "\n"
    r"cross-modal gradient coupling $\Gamma_k=\langle\nabla_{M_k}E,u_{M_k}\rangle$. We ask what an"
    "\n"
    r"admissible allocation statistic can be, and show that the five requirements of Section~III"
    "\n"
    r"force it to be additive in the per-block contributions---additivity being an assumption"
    "\n"
    r"rather than a consequence, since block decomposability alone admits $\|\nabla E\|^2$. Given"
    "\n"
    r"it, $\Gamma$ is unique up to positive scaling and the allocation is"
    "\n"
    r"$\mathrm{rank}_k\propto\exp(-\beta|\Gamma_k|)$."
    "\n\n"
    r"Measured on CLIP, $\Gamma$ predicts a rank allocation for LLaVA instruction tuning with no"
    "\n"
    r"target-model gradient. At identical trainable-parameter counts the allocation beats the"
    "\n"
    r"uniform-rank baseline at one learning rate, but the advantage reverses at another and"
    "\n"
    r"vanishes under matched training loss, so we report a zero-shot heuristic, not an optimum."
    "\n"
    r"Three controls bound its scope: it is indistinguishable from a random allocation of the same"
    "\n"
    r"budget; AdaLoRA, swept over the same rates, reaches lower alignment energy than any of our"
    "\n"
    r"arms; and the critical rank we had bracketed at $r_c\in[5,6]$ belongs to the protocol, not"
    "\n"
    r"to the model. That protocol is the largest caveat: its inputs are blank images, and at the"
    "\n"
    r"paper's operating point a blank image carries three times the initialization alignment"
    "\n"
    r"energy of a real one, so the objective optimised is not the one a real input induces."
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
    print(f"  旧 {count_words(t[i:end])} 词 → 新 {count_words(NEW)} 词")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = MAIN.with_suffix(".tex.bak_p488")
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
        "additivity 是假设非推论": "an assumption" in ab and "rather than a consequence" in ab,
        "含反例": "$\\|\\nabla E\\|^2$" in ab,
        "r_c 属协议": "belongs to the protocol" in ab,
        "含 matched training loss": "matched training loss" in ab,
        "含与随机不可区分": "indistinguishable from a random allocation" in ab,
        "含 AdaLoRA 更优": "reaches lower alignment energy" in ab,
        "含 blank 3×": "three times the initialization" in ab,
        "定位为 heuristic 非 optimum": "zero-shot heuristic, not an optimum" in ab,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
