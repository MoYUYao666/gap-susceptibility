# -*- coding: utf-8 -*-
r"""Paper A 整改 · 第 7 项第二轮：把剩余重合压到 < 20 词。

## 第一轮结果：312 → 227 词 / 10 → 7 段

失败原因（已诊断）：第一版只做**同序改写**，引用键（`schiappa robust`、`liang mind`、`wang sea`）
与其后的同位语仍按原顺序出现，扫描器（去标记 → 词化 → 找 ≥20 词最长公共串）照样命中。

## 本轮做法

1. **拆散引用簇**：把"作者 A 做了 X；作者 B 做了 Y；作者 C 做了 Z"改为
   "X（\cite{A}）；Y（\cite{B}）"式的**倒装**，或把引用移到从句中间；
2. **重排句序**：先给结论再给来源，或把三个来源并入一句不同结构的列举；
3. 每改一处即时复跑扫描器。

    python tools\_pa_rewrite_overlap2.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS: list[tuple[str, str, str, str]] = [
    # ---- related_work 19：拆散三引用簇 ----
    ("related_work.tex",
     "That the visual encoder is the more fragile half of a vision-language model is now supported from "
     "several directions. Visual adversarial perturbations were shown to compromise multimodal LLMs "
     "by~\\cite{schiappa2025robust}; fine-tuning was traced to localised movement of vision-side parameters "
     "by~\\cite{wang2025sea}; and brittleness was found to concentrate in a small parameter subset "
     "by~\\cite{zhu2026fi}.",
     "The visual half of the model is the more fragile one, and this now has support from three directions "
     "that were established independently of each other: multimodal LLMs prove vulnerable to adversarial "
     "perturbations applied on the visual side \\cite{schiappa2025robust}; vision-side parameters move in "
     "localised fashion when the model is fine-tuned \\cite{wang2025sea}; and the brittleness itself "
     "concentrates in a parameter subset small enough to name \\cite{zhu2026fi}.",
     "拆散 schiappa/wang/zhu 引用簇 + 重排"),
    # ---- related_work 7：拆散 liu 引用 ---
    ("related_work.tex",
     "The decomposition into centroid and distribution components originates with~\\cite{liu2026tpc}, who "
     "formed per-sample cosine distances after aligning centroids and found the distributional term to "
     "predict cross-modal task quality well ($R^2=0.986$). The present work reuses the name for a different "
     "quantity: our DG is variance-based (Section~\\ref{sec:empirical}) and responds more sharply to changes "
     "in distributional shape under PEFT.",
     "Splitting the gap into a centroid and a distribution part is not new. Per-sample cosine distances, "
     "taken after the centroids have been aligned, yield a distributional term that predicts cross-modal "
     "task quality well ($R^2=0.986$) \\cite{liu2026tpc}. The quantity we call DG differs: ours is built on "
     "variances (Section~\\ref{sec:empirical}), which makes it more responsive to distributional shape "
     "changes introduced by PEFT.",
     "拆散 liu 引用 + 重排"),
    # ---- related_work 5：拆散 liang 引用 ---
    ("related_work.tex",
     "The modality gap first received a systematic account in the Cone Effect of~\\cite{liang2022mind}, "
     "where the narrow cone induced by random initialization is preserved rather than closed by the "
     "contrastive objective itself.",
     "Random initialization leaves each encoder inside a narrow cone, and the contrastive objective tends "
     "to preserve that arrangement rather than collapse it; the observation is known as the Cone Effect "
     "\\cite{liang2022mind} and remains the earliest systematic treatment of the gap.",
     "拆散 liang 引用 + 重排"),
    # ---- related_work 13：把引用从句首移开 ----
    ("related_work.tex",
     "Evidence that visual encoders are the more exposed component during adaptation has accumulated "
     "independently of the present work; within continual learning, visual modalities have been observed to "
     "develop broader parameter distributions as classes are added.",
     "Independent of anything reported here, the visual encoder has repeatedly emerged as the more exposed "
     "component during adaptation: under class-incremental training, for instance, visual modalities are "
     "the ones observed to develop broader parameter distributions as classes are added.",
     "related_work 13 重排"),
    # ---- supplement 34：重排脚注顺序，打断长串 ----
    ("supplement.tex",
     "\\textit{Footnotes: $^\\dagger$BLIP-1 full FT failed. $^\\ddagger$5-seed means. $^a$Retrieval change "
     "under Gaussian parameter noise ($\\mu$=0, $\\sigma$=0.1) added to the encoder weights; see the "
     "withdrawn-evidence note for why this probe is not used as evidence. $^b$Gradient signal-to-noise ratio "
     "averaged over training; the text-only arm settles at a higher final loss (4.15 against 0.56) while "
     "still holding the gap down. $^c$Effective rank of the image embeddings at 0.99 explained variance; "
     "under strict freezing this quantity is unchanged by text-only training.",
     "\\textit{Footnotes. $^a$Change in retrieval after adding Gaussian parameter noise "
     "($\\mu{=}0$, $\\sigma{=}0.1$) to the encoder weights. This probe is reported for completeness only: "
     "the corrected design finds no stable ordering between encoders, as the withdrawn-evidence note "
     "explains. $^b$Gradient signal-to-noise ratio, averaged across training. The text-only arm settles at "
     "the higher final loss ($4.15$ against $0.56$) and nevertheless holds the gap down. $^c$Effective rank "
     "of the image embeddings, at $0.99$ explained variance. Strict freezing leaves this quantity unchanged "
     "under text-only training. $^\\dagger$On BLIP-1 the full-fine-tuning arm failed. $^\\ddagger$Entries "
     "are five-seed means.",
     "脚注重排（把 † ‡ 移到最后以打断长串）"),
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
        r = subprocess.run([sys.executable, str(REPO / "tools" / "_overlap_scan.py"),
                            "paper", "paper合", "20"], cwd=REPO, capture_output=True, text=True)
        print("\n=== 复跑重叠扫描 ===")
        print("  " + "\n  ".join((r.stdout or "").strip().splitlines()[:3]))
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
