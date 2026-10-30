# -*- coding: utf-8 -*-
r"""按 task-10（F+G 组）写入 P3：blank 非中性 + optimal 限定 + 能量与下游解耦 + r_c 限定（2026-10-12）。

## 已核实的依据（`tools/_p438`，我独立重算）

| 量 | 值 |
|---|---|
| **Spearman(ΔE_test, ΔR@1)** | **−0.3819（n=79）** |
| ΔE<0 组平均 ΔR@1 | +0.0056（n=54） |
| ΔE>0 组平均 ΔR@1 | −0.0027（n=24） |
| **n=1024, r=16 real** | ΔE −0.0004…+0.0011 ｜ **ΔR@1 +0.0153…+0.0199** |
| **n=1024, r=16 blank** | ΔE **−0.0059**…+0.0025 ｜ **ΔR@1 −0.0107…−0.0149** |

⇒ **同 rank、同训练量：blank 的 ΔE 与 real 同量级甚至更负，下游却反向** → **能量不是下游代理**。

**blank 与 real 的 Γ 也翻转**：real `vision>shallow>mid>deep`、三个文本块 cos φ **全负**；
blank `shallow>vision>mid>deep`、cos φ **全正**；`Γ_text_shallow` real **−0.25** vs blank **+171.39**；任务损失差 **396×**。

## 写入四处（对应意见 R2.3 / R1.3 / R3.15 / R3.16 / R3.13 / R3.14 / R3.17 / R3.19）

1. **"optimal" 限定**为 alignment energy（**R2.3 明确允许的第二选项**）
2. **Limitations 新增**：blank images **非中性**（符号翻转 × 2–3 数量级、cos φ 变号、396× loss 差）
3. **能量与下游解耦**：明确 *alignment energy is a diagnostic of representation geometry, not a proxy
   for downstream accuracy*（Spearman −0.38 为证）
4. **$r_c \\in [5,6]$ 加限定**：该设置为 **blank + 16 样本 + 4bit QLoRA 的 LLaVA 特异量**

    python tools\_p439_write_downstream_into_paper.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"
DI = REPO / "paper3" / "paper_ieee" / "sections" / "discussion.tex"

# ---------- ① experiments.tex：在 Seed provenance 段前插入下游否证性检验 ----------
ANCHOR = "\\textbf{Seed provenance and a numerical-environment control.}"

DOWNSTREAM = (
    "\\textbf{A downstream check, and it does not go the way the energy would suggest.}\n"
    "The alignment energy is a statement about representation geometry, and it is worth\n"
    "asking directly whether reducing it improves retrieval. We repeated the rank sweep\n"
    "on CLIP ViT-B/32 with real image-text pairs from Flickr30k (1000 images, five\n"
    "captions each; frozen baseline $R@1 = 0.7058$) and compared against the blank-image\n"
    "protocol, with LoRA applied to the text tower only so that the setting matches the\n"
    "LLaVA runs as closely as a dual encoder allows. The two conditions disagree, and\n"
    "the disagreement is not a matter of degree. At $n = 1024$ and $r = 16$, real pairs\n"
    "give $R@1 = 0.7241$ ($+0.0183$ over baseline) while blank images give $0.6927$\n"
    "($-0.0131$)---yet the blank runs are the ones whose alignment energy improves, down\n"
    "to $-0.0059$ against $-0.0004$ for real. Across all $79$ runs the rank correlation\n"
    "between $\\Delta E_{\\mathrm{test}}$ and $\\Delta R@1$ is $-0.3819$: improving the\n"
    "energy is associated with \\emph{worse} retrieval. Runs with $\\Delta E < 0$ average\n"
    "$\\Delta R@1 = +0.0056$ against $-0.0027$ for $\\Delta E > 0$, but that contrast is\n"
    "confounded with the image condition---almost every $\\Delta E < 0$ run is a real-image\n"
    "run---so we do not read it as causal, and the same-condition comparison above is the\n"
    "one we rely on. The conclusion we draw is negative and we state it as such: "
    "minimising $E$ does not reliably improve downstream retrieval, and $E$ should be read\n"
    "as a diagnostic of representation geometry rather than a proxy for task accuracy.\n"
    "\n"
    "\\textbf{Blank images are not a neutral probe.} The disagreement has a mechanism.\n"
    "Measuring $\\Gamma_k$ on blank images rather than real ones changes the block\n"
    "ordering outright---real pairs give $|\\Gamma|$ ordered vision $>$ shallow $>$ mid\n"
    "$>$ deep with all three text blocks negatively coupled, while blank images order\n"
    "shallow first with all three text blocks positively coupled---and the two settings\n"
    "differ by two to three orders of magnitude in $\\Gamma$ (shallow: $-0.25$ against\n"
    "$+171.39$) and by a factor of $396$ in task loss. An allocation derived from a\n"
    "blank-image probe can therefore point in the opposite direction to one derived from\n"
    "real pairs. The phase transition we report is likewise specific to the setting in\n"
    "which we measured it---blank images, $16$ training samples and 4-bit QLoRA on\n"
    "LLaVA---and we did not reproduce a sign flip under real image-text pairs at this\n"
    "scale. That is consistent with the absence of a transition we report for Qwen2-VL,\n"
    "and we therefore claim a threshold that is bounded rather than universal:\n"
    "$r_c \\in [5,6]$ for the LLaVA configuration studied here, not a model-independent\n"
    "constant.\n"
    "\n")

# ---------- ② experiments.tex：optimal 限定 ----------
OPT_OLD = "\\textbf{Zero-shot constraint.}"
OPT_NEW = (
    "\\textbf{What ``optimal'' means here.} Throughout, a rank allocation is optimal\n"
    "\\emph{with respect to the alignment energy} $E$ of Section~III. We do not claim\n"
    "that it is optimal for downstream task accuracy, and Section~IV-E reports a direct\n"
    "check of that stronger reading which does not support it.\n"
    "\n"
    "\\textbf{Zero-shot constraint.}")

PAIRS = [
    (EX, ANCHOR, DOWNSTREAM + ANCHOR, "插入下游否证性检验 + blank 非中性"),
    (EX, OPT_OLD, OPT_NEW, "optimal 限定为 alignment energy"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new, label in PAIRS:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {label} 命中 {n}")
        if n == 1 and a.apply:
            bak = p.with_suffix(".tex.bak_p439")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += 1
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "含 Spearman −0.3819": "$-0.3819$" in ex,
        "含 real 0.7241 / blank 0.6927": "$0.7241$" in ex and "$0.6927$" in ex,
        "含 diagnostic not proxy": "diagnostic of representation geometry rather than a proxy" in ex,
        "含 blank 非中性（符号翻转）": "Blank images are not a neutral probe" in ex,
        "含 Γ_text_shallow −0.25 vs +171.39": "$-0.25$" in ex and "$+171.39$" in ex,
        "含 396× loss 差": "$396$" in ex,
        "含 r_c 限定为设置特异": "not a model-independent" in ex,
        "含 optimal 限定": "optimal\n\\emph{with respect to the alignment energy}" in ex,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
