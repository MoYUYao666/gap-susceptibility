# -*- coding: utf-8 -*-
r"""重写稿中的"同预算分配比较"段（对称 lr 扫描后的最终口径）（2026-10-13）。

## 为什么必须**重写**（而非改数字）

对称 lr 扫描给出**对我方主张最强的反证**（`tools/_p475` 写的版本已被推翻）：

| 方案 | lr | n | ΔE 均值 | **loss_last** |
|---|---|---|---|---|
| `exp` | 5e-5 | 6 | **+1477.5** | 1.3762 |
| `uniform` | 5e-5 | 6 | **+5047.5** | 1.3734 |
| **`exp`** | **3e-4** | 2 | **+5967.8** | **0.5872** |
| **`uniform`** | **3e-4** | 2 | **+2842.1** | **0.5826** |
| `exp` | 1e-3 | 2 | +2867.4 | 0.2402 |
| `uniform` | 1e-3 | 2 | +4935.8 | 0.2294 |
| *AdaLoRA* | 3e-4 / 1e-3 | 1 | **−1468.2 / −757.3** | 1.4866 / 0.9767 |

**⇒ 三条**：
1. **"Γ-guided 优于 uniform"随 lr 反转**（5e-5 优、**3e-4 劣**、1e-3 优但 `uniform` sd=9084）
2. **匹配任务损失后优势消失**：3e-4 两侧 loss 匹配（**0.5872 vs 0.5826**），
   **`exp` 落后**（+5968 vs +2842）⇒ **5e-5 下的优势很可能是"训练得更少"的副产物**
3. **AdaLoRA 对称调 lr 后仍优于全部 Γ 侧方案**

**⇒ 我先前写的"this allocation beats the uniform-rank baseline"必须删除。**

    python tools\_p480_rewrite_alloc_final.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

START = "and, in a capacity-matched comparison run with six seeds per arm,"
END_MARK = "allocation rather than by differences \\emph{between} allocations."

NEW = (
    "and we ran the comparative controls that this question requires. In a\n"
    "capacity-matched comparison---every arm at exactly $7{,}237{,}632$ trainable\n"
    "parameters, verified per run---the $\\Gamma$-guided allocation beats the uniform-rank\n"
    "baseline at the learning rate we had been using throughout ($\\Delta E = +1478 \\pm 1563$\n"
    "against $+5048 \\pm 1900$ over six seeds, Welch $p = 0.0055$). That comparison does not\n"
    "survive being repeated at other learning rates, and we report the failure rather than\n"
    "the first result. Sweeping both arms over the same range: at $3 \\times 10^{-4}$ the\n"
    "ordering \emph{reverses} ($+5968 \\pm 4775$ against $+2842 \\pm 876$, two seeds each),\n"
    "and at $10^{-3}$ it returns but with the uniform arm spread over $\\pm 9084$, spanning\n"
    "$-1487$ to $+11359$. The decisive control is not the learning rate but the training\n"
    "loss. At $3 \\times 10^{-4}$ the two arms reach nearly the same loss ($0.5872$ against\n"
    "$0.5826$) and there the $\\Gamma$-guided allocation is \emph{worse}: $+5968$ against\n"
    "$+2842$. Read together, the advantage at the lower rate is most plausibly a\n"
    "side-effect of training less far, not a property of the allocation rule, and we\n"
    "therefore no longer claim that the rule beats the uniform baseline on $\\Delta E$.\n"
    "Two further controls point the same way. Against a random allocation of an identical\n"
    "parameter budget---thirty runs over ten distinct feasible allocations---the\n"
    "$\\Gamma$-guided mean ($+1478$) sits at the $47$th percentile of the pool\n"
    "($+3347 \\pm 4771$), with three of the ten random allocations averaging lower.\n"
    "Reversing the rule---largest rank on the \\emph{least} coupled block---does not differ\n"
    "from uniform once the sample is doubled ($+2470 \\pm 4111$, $p = 0.21$); at three seeds\n"
    "it had appeared to ($p = 0.037$), which we record as a small-sample artefact.\n"
    "\n"
    "\\textbf{An adaptive baseline is better on this metric, and we say so.} We implemented\n"
    "AdaLoRA at the same trainable-parameter count and swept its learning rate over the\n"
    "same range as our own arms. At $5 \\times 10^{-5}$ it barely trains (loss\n"
    "$1.5595 \\to 1.5604$), but at $3 \\times 10^{-4}$ and $10^{-3}$ it does\n"
    "($-4.6\\%$ and $-36.8\\%$) and then reaches $\\Delta E = -1468$ and $-757$, against\n"
    "$+1478$ for the best allocation rule we have. The advantage of AdaLoRA is therefore\n"
    "not an artefact of tuning it and not of tuning us---both sides were swept over the\n"
    "same range---and on this metric, at this scale, the adaptive method wins. We note in\n"
    "passing that its lower-loss run is also the less stable one: at $10^{-3}$ the\n"
    "alignment energy spikes to $27{,}331$ before settling, whereas the $3 \\times 10^{-4}$\n"
    "run decreases monotonically.\n"
    "\n"
    "\\textbf{What the rule is for.} The contribution of the $\\Gamma$ statistic is not that\n"
    "it allocates better than a search, but that it allocates \\emph{without searching}:\n"
    "$\\Gamma_k$ is computable from the source model and a reference batch, and the\n"
    "allocation decision never touches a gradient of the target model. That is the regime\n"
    "the rule is designed for---settings where the target cannot be trained repeatedly, or\n"
    "where a per-target hyperparameter search is not available. Where such a search\n"
    "\\emph{is} affordable, a method like AdaLoRA should be preferred, and our results say\n"
    "it should. We also record the resolution limit that makes every comparison above\n"
    "weaker than it looks: with the between-allocation spread at $3010$ and the\n"
    "within-allocation seed spread at $3197$, distinguishing allocations separated by\n"
    "$3570$ would need roughly $11$ to $28$ seeds per arm, of which we report six. What we\n"
    "can state without qualification is the shape of the noise: it is dominated by\n"
    "seed-to-seed variation \\emph{within} a fixed allocation rather than by differences\n"
    "\\emph{between} allocations.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    i = t.find(START)
    j = t.find(END_MARK, i)
    if i < 0 or j < 0:
        print(f"  🔴 锚点未命中（i={i}, j={j}）")
        return 1
    end = j + len(END_MARK)
    old = t[i:end]
    print(f"  将替换 {len(old)} 字符（新 {len(NEW)} 字符）")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p480")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t[:i] + NEW + t[end:])
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "删除'beats the uniform-rank baseline'的旧结论": "The rule therefore beats the uniform-rank baseline" not in t2,
        "含 5e-5 的 p=0.0055 但仍报失败": "$p = 0.0055$" in t2 and "does not\nsurvive" in t2,
        "含 3e-4 反转": "ordering \\emph{reverses}" in t2,
        "含 loss 匹配（0.5872 vs 0.5826）": "$0.5872$" in t2 and "$0.5826$" in t2,
        "含'训练得更少'的解释": "side-effect of training less far" in t2,
        "明确不再主张优于 uniform": "no longer claim that the rule beats" in t2,
        "含 AdaLoRA 更优的如实陈述": "the adaptive method wins" in t2,
        "含 AdaLoRA 两侧同范围扫描": "both sides were swept over the\nsame range" in t2,
        "含'规则的用途是不搜索'": "allocates \\emph{without searching}" in t2,
        "含 AdaLoRA 能量尖峰": "$27{,}331$" in t2,
        "含 11–28 的功效上限": "roughly $11$ to $28$ seeds" in t2,
        "含噪声主要在组内": "within a fixed allocation rather than by differences" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
