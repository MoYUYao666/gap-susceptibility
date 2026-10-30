# -*- coding: utf-8 -*-
r"""Paper A 整改 · 第 5 项（重头戏）：[M1]/[M2] 三条因果证据线的修正。

## 判定（全部基于源数据，非推断）

### ① 噪声敏感性 —— **撤回**（`outputs/noise_fixed_aug.json`）

| σ | 视觉 mean±sd | 文本 mean±sd | ratio | paired p | 视>文 seeds |
|---|---|---|---|---|---|
| 0.03 | −1.022 ± 1.758 | −2.190 ± 0.516 | **0.467** | 0.256 | 3/5 |
| 0.10 | 1.898 ± 1.832 | 2.482 ± 3.248 | **0.765** | **0.7718** | 2/5 |

σ=0 对照 **完美复现基线**（`control_sigma0_reproduces_baseline: true`）。
→ 旧文的 **"2.6×"** 在任何 σ 下都不成立；**文本侧反而略更敏感且不显著** → **该证据线撤回**。
（ap3 已作同样处理并给出相同数字，`备选/06_归档稿件/paper_ap3/sections/04_mechanism.tex`）

### ② 梯度贡献 —— **1.5× → 1.41×**（`outputs/gsnr_results.json`）

`vis_grad_norm 0.5282468` / `txt_grad_norm 0.3743503` = **1.4111**，文件内字段 `v_t_ratio` 即 1.411。
旧文写 "1.5×" 系向上取整。

### ③ 有效秩 —— **"零视觉扰动" 改为严格冻结实测**（`outputs/analysis/strict_control_summary.json`）

严格冻结（视觉侧 `vision_nonzero_tensors = 0`，199 张量）下：
- `text_only`：可训 **196,608**，`vision_rank_delta_mean` = **0.0000**（视觉几何逐层不变）
- `both`：可训 491,520，`vision_rank_delta_mean` = **−0.0421**
- `vision_only`：可训 294,912，`vision_rank_delta_mean` = **−0.0588**

而**旧（未冻结）** text-only 跑到 **145,170,177** 参数（≈96%），故其"视觉侧变化"是冻结失效的假象。

    python tools\_pa_fix_m1_evidence.py            # 预演
    python tools\_pa_fix_m1_evidence.py --apply
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS: list[tuple[str, str, str, str]] = [
    # ---- 1) 三条线 → 两条线 ----
    ("empirical.tex",
     "Why does text-only preserve alignment? We propose the \\textbf{Visual Fragility Interpretation}: "
     "visual embedding spaces are more sensitive to parameter perturbation than text spaces. "
     "Three independent lines of causal evidence support this interpretation.",
     "Why does text-only preserve alignment? We propose the \\textbf{Visual Fragility Interpretation}: "
     "intervening on the visual side of a vision-language model is what damages cross-modal alignment, "
     "whereas leaving it untouched preserves it. Two evidence lines support this interpretation, and one "
     "earlier line is withdrawn in favour of them.",
     "三条线 → 两条线 + 指明有一线撤回"),
    # ---- 2) 噪声敏感性：撤回 ----
    ("empirical.tex",
     "\\textbf{Noise sensitivity.} We inject isotropic Gaussian noise into encoder parameters and measure "
     "retrieval degradation. Vision encoder noise causes $2.6\\times$ greater degradation than comparable "
     "text encoder noise, confirming that visual representations depend on more precisely tuned parameters.",
     "\\textbf{Noise sensitivity (withdrawn).} An earlier single evaluation of isotropic Gaussian noise in the "
     "encoder parameters suggested that vision-side noise degrades retrieval $2.6\\times$ more than text-side "
     "noise. Repeating the probe with the image set and the augmentation draw held fixed across conditions, "
     "and with a $\\sigma{=}0$ control that reproduces the baseline exactly, gives no stable ordering over "
     "five seeds ($1.90 \\pm 1.83\\%$ for the vision encoder against $2.48 \\pm 3.25\\%$ for the text encoder "
     "at $\\sigma{=}0.1$, paired $p = 0.77$; the ratio of means is $0.77$, i.e.\\ the text side is nominally "
     "the more sensitive of the two). This evidence line is therefore **not used**, and the $\\sigma{=}0$ "
     "control is retained in the released artefact.",
     "噪声敏感性撤回（含实测值与 p 值）"),
    # ---- 3) GSNR 1.5× → 1.41× ----
    ("empirical.tex",
     "The vision GSNR exceeds the text GSNR by $1.5\\times$, indicating that visual parameters experience "
     "stronger optimization pressure during standard fine-tuning.",
     "During joint-modality fine-tuning the vision encoder's gradient norm exceeds the text encoder's by "
     "$1.41\\times$ ($0.528$ against $0.374$, single measurement on the reference configuration), indicating "
     "that visual parameters experience stronger optimization pressure under joint training. We report the "
     "measured ratio rather than a rounded one, and note that it rests on a single measurement.",
     "GSNR 1.5× → 1.41×（实测）+ 单次测量的诚实披露"),
    # ---- 4) 有效秩：改为严格冻结实测 ----
    ("empirical.tex",
     "\\textbf{Effective rank collapse.} We track the effective rank of weight updates $\\|\\Delta W\\|_F$ per "
     "encoder layer. Text-only training has zero vision-side weight perturbation by construction; "
     "joint-modality training produces substantial vision-side weight changes, with magnitude increasing with "
     "LoRA rank. This links directly to the ODE prediction: higher visual-side perturbation corresponds to "
     "larger $\\bar{\\Gamma}_v\\|g_v\\|$ in the perturbation force $\\alpha$.",
     "\\textbf{Effective rank under strict control.} We track the effective rank of the per-layer image "
     "embeddings under a strictly frozen protocol, in which the optimizer sees only the adapter matrices "
     "($196{,}608$ trainable parameters for the text-only arm) and the vision side registers zero non-zero "
     "updates across all $199$ vision tensors. Under that control, text-only training leaves the vision-side "
     "effective rank unchanged to measurement precision (mean per-layer change $0.000$), whereas the "
     "both-position arm lowers it by $0.042$ and the vision-only arm by $0.059$ on the same scale. This "
     "links directly to the ODE prediction: larger visual-side perturbation corresponds to a larger "
     "$\\bar{\\Gamma}_v\\|g_v\\|$ in the perturbation force $\\alpha$. We flag the contrast with the archived "
     "non-strict runs, in which the text-only arm trained $145{,}170{,}177$ parameters including the vision "
     "encoder, so any vision-side change measured there is a property of that setup rather than of "
     "text-only adaptation.",
     "[M1]+[M2]：零扰动改为严格冻结实测 + 披露旧协议差异"),
    # ---- 5) 收尾句：三条→两条 ----
    ("empirical.tex",
     "We emphasize that Visual Fragility is a phenomenological interpretation supported by converging evidence, "
     "not a deductively proven mechanism.",
     "We emphasize that Visual Fragility is a phenomenological interpretation supported by the evidence above, "
     "not a deductively proven mechanism.",
     "收尾句同步"),
    # ---- 6) 贡献列表：去掉 "three converging lines of causal evidence" ----
    ("introduction.tex",
     "and the Visual Fragility Interpretation supported by three converging lines of causal evidence.",
     "and the Visual Fragility Interpretation, supported by strict-freezing controls and spectral evidence.",
     "贡献列表同步"),
    # ---- 7) 摘要/结论若含因果措辞 ----
    ("conclusion.tex",
     "and that visual embedding spaces are inherently more sensitive to parameter perturbation than text spaces "
     "(Visual Fragility Interpretation).",
     "and that what damages cross-modal alignment is intervening on the visual side rather than adapting the "
     "language side (Visual Fragility Interpretation, supported by strict-freezing controls).",
     "结论同步（去掉「视觉空间天生更敏感」的因果措辞）"),
    # ---- 8) 图注 2.6× → 撤回 ----
    ("supplement.tex",
     "\\caption{Parameter noise sensitivity and effective rank tracking. (A) Vision encoder degrades "
     "2.6$\\times$ more than text encoder under equivalent parameter noise.",
     "\\caption{Parameter noise sensitivity and effective rank tracking. (A) Parameter-noise probe; note "
     "that the corrected probe finds no stable ordering between encoders (see the withdrawn-evidence note "
     "in the main text), so this panel is retained for transparency only.",
     "图注 (A) 的 2.6× 撤回"),
    # ---- 9) 图注 "zero vision-side weight change" ----
    ("supplement.tex",
     "(A) Mean $\\|\\Delta W\\|_F$ per encoder: text-only has zero vision-side weight change.",
     "(A) Mean $\\|\\Delta W\\|_F$ per encoder. Under strict freezing the text-only arm trains no vision "
     "parameters at all, so its vision-side update is identically zero.",
     "图注 (A) 改为严格冻结口径"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for fname, old, new, why in EDITS:
        p = S / fname
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {fname}: {why}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        elif c == 0:
            print(f"  ⚠ {fname}: 未命中（{why}）")
        else:
            print(f"  ⚠ {fname}: 命中 {c} 次，拒绝改动（{why}）")
    print(f"\n{n}/{len(EDITS)} 处{'已改' if apply else '可改'}")
    if apply:
        bad = []
        for f in S.glob("*.tex"):
            tt = io.open(f, encoding="utf-8").read()
            for pat in ("2.6$\\times$", "1.5$\\times$", "zero vision-side weight perturbation by construction",
                        "Three independent lines", "three converging lines of causal"):
                if pat in tt:
                    bad.append(f"{f.name}:{pat}")
        assert not bad, f"仍有旧主张残留：{bad}"
        print("✅ 断言通过：三条旧主张已全部替换")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
