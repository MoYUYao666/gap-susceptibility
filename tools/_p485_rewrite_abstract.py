# -*- coding: utf-8 -*-
r"""重写摘要：清除与正文矛盾/已被撤回的主张（2026-10-13）。

## 🔴 我核出的摘要-正文矛盾（都源自同一原因：正文改了 26 处，摘要没跟着改）

| # | 摘要现状 | 正文现状 | 严重度 |
|---|---|---|---|
| 1 | *"reduces uncertainty by **$30\times$**"* | **正文已删**："$30\\times$ ratio **must not** be read as $\\Gamma$ reducing allocation uncertainty"（$\\eta^2=0.989$、同秩 sd 比 0.98） | 🔴 **直接矛盾** |
| 2 | *"the **unique** scalar (up to positive scaling) satisfying the axioms"* | 正文：**R3 不足以推出唯一性**，需**新增 R3′**（且已给反例 $\\|x\\|^2$） | 🔴 |
| 3 | *"an alignment **phase transition** at critical rank $r_c\\in[5,6]$"* | 正文：**降级为"location is bracketed"**（CI 跨零、置换 p=0.100、功效不足） | 🔴 |
| 4 | *"190 runs (181 sweep + 9 counterfactual) across 2 architectures and 4 sample sizes"* | 现有 **79 + 43 + 4 = 126 run** 且实验已换协议；旧计数含 $E_2$/`extra`/`sweep` | ⚠️ 需核 |
| 5 | 未提 blank-image 非中性 / 未提 AdaLoRA 更优 / 未提"分配不含目标模型梯度"的定位 | 正文三处新增小节 | ⚠️ 缺失 |
| 6 | 未提 $\\beta$ 来源更正、rank-vs-参数记账 | 正文已改 | ⚠️ 缺失 |

**⇒ 摘要必须重写。** 这也是**"改了正文没改摘要"**——本项目"数字随数据更新、旧值必须被替换而非留在别处"的又一次实例。

    python tools\_p485_rewrite_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper3" / "paper_ieee" / "main.tex"

START = "We show that optimal PEFT rank allocation"
END = "confirm the framework."

NEW = (
    r"We study how to allocate PEFT rank across the blocks of a multimodal model when the"
    "\n"
    r"target cannot be searched: the decision must be made from the source model alone. The"
    "\n"
    r"central object is the cross-modal gradient coupling coefficient"
    "\n"
    r"$\Gamma_k = \langle \nabla_{M_k}E, u_{M_k}\rangle$. We first ask what an admissible"
    "\n"
    r"allocation statistic can be, and show that under five requirements---pre-training"
    "\n"
    r"computability, invariance under block-wise orthogonal reparameterisation, block"
    "\n"
    r"decomposability, sign consistency with alignment, and first-order observability---"
    "\n"
    r"a statistic must be additive in the per-block contributions, and that this last"
    "\n"
    r"property is an additional structural assumption rather than a consequence: block"
    "\n"
    r"decomposability alone does not imply it, as $\|\nabla E\|^2$ demonstrates. With it"
    "\n"
    r"stated explicitly, $\Gamma$ is the unique representative up to positive scaling, and"
    "\n"
    r"constrained optimisation gives the exponential allocation"
    "\n"
    r"$\mathrm{rank}_k \propto \exp(-\beta|\Gamma_k|)$."
    "\n\n"
    r"We validate by zero-shot transfer: $\Gamma$ measured on CLIP predicts a rank"
    "\n"
    r"allocation for LLaVA instruction tuning without any target-model gradient, an"
    "\n"
    r"encoder-only to decoder-based transfer. In a capacity-matched comparison---every arm"
    "\n"
    r"at exactly the same trainable-parameter count---the $\Gamma$-guided allocation beats"
    "\n"
    r"the uniform-rank baseline at one learning rate, but the advantage reverses at another"
    "\n"
    r"and disappears once the two arms are matched on training loss, so we report the"
    "\n"
    r"allocation as a zero-shot heuristic rather than as an optimum. Three controls bound"
    "\n"
    r"the scope: the rule is indistinguishable from a random allocation of the same budget;"
    "\n"
    r"an adaptive method (AdaLoRA), swept over the same learning rates, reaches lower"
    "\n"
    r"alignment energy than any of our arms; and the critical rank we had bracketed at"
    "\n"
    r"$r_c \in [5,6]$ is a property of the measurement protocol, not a model-independent"
    "\n"
    r"constant. That protocol is itself the largest caveat: its visual inputs are blank"
    "\n"
    r"images, and at the paper's own operating point a blank image carries three times the"
    "\n"
    r"initialization alignment energy of a real one, so the objective being optimised is"
    "\n"
    r"not the objective a real multimodal input induces. We close by delimiting what the"
    "\n"
    r"rule is for: allocating without searching, not allocating better than a search."
    "\n")


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
    n_words = len(old.split())
    print(f"  旧摘要正文 {n_words} 词 → 新 {len(NEW.split())} 词")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = MAIN.with_suffix(".tex.bak_p485")
    if not bak.exists():
        shutil.copy2(MAIN, bak)
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t[:i] + NEW + t[end:])
    t2 = io.open(MAIN, encoding="utf-8", errors="replace").read()
    checks = {
        "删掉 30× 主张": "$30\\times$" not in t2 and "reduces uncertainty" not in t2,
        "unique 已限定（需 R3′）": "additional structural assumption" in t2,
        "含反例 ‖∇E‖²": "$\\|\\nabla E\\|^2$" in t2,
        "phase transition 已降级为 bracketed": "we had bracketed" in t2,
        "删掉旧 run 计数 190": "190 runs" not in t2,
        "含容量匹配 + 优势反转 + loss 匹配": "disappears once the two arms are matched" in t2,
        "含与随机不可区分": "indistinguishable from a random allocation" in t2,
        "含 AdaLoRA 更优": "reaches lower" in t2 and "AdaLoRA" in t2,
        "含 blank 3× 与协议归属": "three times the" in t2,
        "含定位句": "allocating without searching" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    # 词数（PRL 要求 ≤250）
    ab = t2[t2.find("\\begin{abstract}"):t2.find("\\noindent\\textbf{Keywords")]
    import re
    w = len(re.sub(r"\\[a-zA-Z]+|[{}$\\]", " ", ab).split())
    print(f"  → 粗估摘要词数 ≈ {w}（PRL 上限 250）")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
