# -*- coding: utf-8 -*-
r"""施加 Visual Fragility 限定 + 过强概化句（PR R2.4/R3.3/R1.4）（2026-10-12）。

## 依据

`tools/_p255`（task-2，426 条件）：**匹配相对扰动下 vision 塔并不更脆弱**
（预算比 0.912±0.452 / 0.989±0.449 / 1.061±0.435），且**方向随协议翻转**
（匹配相对 = 0.60 vs 等绝对 = 2.47）。

→ 因此：
- "Visual Fragility" 只能作为**关于适配器放在哪里**的解释，**不能**作为
  "视觉塔本质更脆弱"的因果结论；
- `inherently more sensitive`、`guaranteed alignment protection`、
  `apply to any contrastive backbone`、`regardless of adapter capacity` 等
  **均超出证据**，须限定。

    python tools\_p281_hedge_fragility.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAIRS = [
    # --- empirical.tex ---
    ("paper合/sections/empirical.tex",
     r"\subsection{Visual Fragility Interpretation}",
     r"\subsection{Visual Fragility: an Interpretation of Where the Adapters Sit, "
     r"Not of a Fragile Tower}"),

    ("paper合/sections/empirical.tex",
     r"We emphasize that Visual Fragility is a phenomenological interpretation supported by "
     r"the evidence above, not a deductively proven mechanism. Section~\ref{sec:theory} "
     r"provides the formal framework that explains \emph{why} visual fragility emerges from "
     r"gradient geometry.",
     r"We emphasize that Visual Fragility is a phenomenological interpretation supported by "
     r"the evidence above, not a deductively proven mechanism. Two further results constrain "
     r"it. First, under matched \emph{relative} weight perturbation "
     r"($\|\Delta W\|_F/\|W\|_F$ equal per tensor and per tower) the vision tower is not the "
     r"more fragile one: the relative budget each tower needs for the same retrieval loss is "
     r"$0.91\pm0.45$ at a $5\%$ drop and $0.99\pm0.45$ at $10\%$, i.e.\ indistinguishable "
     r"from parity, and the ordering reverses when the comparison is made at equal "
     r"\emph{absolute} noise ($0.60$ versus $2.47$). Second, the archived probe on which the "
     r"$2.6\times$ figure rested used $\sigma\,\mathrm{std}(W_i)$ per tensor and, because its "
     r"LayerNorm filter did not match the HuggingFace parameter names, perturbed LayerNorm "
     r"parameters that carry $73.9\%$ of the vision tower's injected Frobenius norm; at the "
     r"same $\sigma$ the vision tower therefore received a $1.14\times$ larger relative "
     r"perturbation. What the evidence does support is narrower and is the claim we make: "
     r"leaving the vision encoder untouched preserves alignment, so the practical rule "
     r"concerns \emph{where} the adapters are placed. Section~\ref{sec:theory} derives the "
     r"gradient geometry behind that placement effect."),

    # --- introduction.tex ---
    ("paper合/sections/introduction.tex",
     r"suggest that visual embedding spaces are inherently more sensitive to parameter "
     r"perturbation than text spaces.",
     r"suggest that intervening on the visual side is what damages alignment. Whether the "
     r"vision tower is intrinsically more sensitive is a separate question that we test and "
     r"answer negatively under matched relative perturbation (Section~\ref{sec:empirical}), "
     r"so we state the claim about placement rather than about fragility."),

    ("paper合/sections/introduction.tex",
     r"the Visual Fragility Interpretation, supported by strict-freezing controls and "
     r"spectral evidence.",
     r"the Visual Fragility Interpretation of \emph{placement} (adapters on the text side "
     r"leave the vision encoder untouched and the benefit survives strict freezing), which we "
     r"bound explicitly by showing that the tower-level fragility ordering does not survive "
     r"parameter-matched perturbation."),

    # --- conclusion.tex ---
    ("paper合/sections/conclusion.tex",
     r"and that what damages cross-modal alignment is intervening on the visual side rather "
     r"than adapting the language side (Visual Fragility Interpretation, supported by "
     r"strict-freezing controls).",
     r"and that what damages cross-modal alignment is intervening on the visual side rather "
     r"than adapting the language side (Visual Fragility Interpretation, supported by "
     r"strict-freezing controls; we show under matched relative perturbation that this is a "
     r"statement about where the adapters sit, not evidence that the vision tower is "
     r"intrinsically the more fragile one)."),

    # --- discussion.tex ---
    ("paper合/sections/discussion.tex",
     r"Text-only requires no additional implementation and provides guaranteed alignment "
     r"protection.",
     r"Text-only requires no additional implementation. We report the protection it provides "
     r"as an empirical tendency over our archive rather than a guarantee: the gap inflation "
     r"is smaller for text-only in most of our configurations and the ordering reverses on "
     r"SigLIP under strict freezing, so the rule should be verified per backbone."),

    ("paper合/sections/discussion.tex",
     r"These principles require no architectural modification and apply to any contrastive "
     r"vision-language backbone.",
     r"These principles require no architectural modification. They are established here on "
     r"contrastive dual-encoder backbones over image--text retrieval and zero-shot "
     r"classification; the ordering we observe reverses on SigLIP under strict freezing, so "
     r"we do not claim them for architectures or objectives outside that scope."),

    # --- theory.tex / validation.tex ---
    ("paper合/sections/theory.tex",
     r"The task gradient concentrates in a low-dimensional subspace regardless of the "
     r"adapter's capacity.",
     r"The task gradient concentrates in a low-dimensional subspace across the adapter "
     r"capacities we probed (rank $r$ from $1$ to $64$)."),

    ("paper合/sections/validation.tex",
     r"This \textbf{Effective Rank Saturation} reveals that the task gradient concentrates "
     r"in a low-dimensional subspace regardless of adapter capacity.",
     r"This \textbf{Effective Rank Saturation} shows that, over the rank range we probed, the "
     r"task gradient's effective dimension stays in a narrow band rather than growing with "
     r"adapter capacity."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for rel, old, new in PAIRS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        tag = old[:52].replace("\n", " ")
        print(f"  {'✅' if n == 1 else ('⚠️ ' if n == 0 else '🔁')} {Path(rel).name}: {n} ｜ {tag}…")
        if n == 0:
            continue
        if not a.apply:
            continue
        bak = p.with_suffix(p.suffix + ".bak_p281")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        total += n

    if not a.apply:
        print("\n  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
