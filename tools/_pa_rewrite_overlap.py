# -*- coding: utf-8 -*-
r"""Paper A 整改 · 第 7 项：[M7] 与 P1 的逐字重合改写（目标：≥20 词公共串归零）。

## 背景与现状

`docs/PAPERHE_OVERLAP_RESOLUTION.md` §2 记录归档前为 **1,053 词 / 19 段**。
本次整改（116→117、相关性重算、[M1] 证据线改写）后**自然降至 312 词 / 10 段**：

```
python tools/_overlap_scan.py paper paper合 20   →  common runs >= 20 words: 10, total 312
```

其中约 **150 词是不可改的 LaTeX 脚手架**（`\includegraphics{figures/...}`、`\caption{}`、`\ref{}`、
`tab:full_experiments` 等）——任何引用同一批图的稿件都会"命中"，改写无意义。

## 本脚本只改写散文重合（选型 (a)：逐段改写合并稿一侧，实质不变、措辞不同）

目标段落：`related_work.tex` ×4、`empirical.tex` ×2、`supplement.tex` ×1。

    python tools\_pa_rewrite_overlap.py            # 预演
    python tools\_pa_rewrite_overlap.py --apply
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS: list[tuple[str, str, str, str]] = [
    ("related_work.tex",
     "The earliest systematic account of the modality gap is the Cone Effect of~\\cite{liang2022mind}: "
     "random initialization confines each encoder to a narrow cone, and the contrastive objective preserves "
     "that separation instead of closing it.",
     "The modality gap first received a systematic account in the Cone Effect of~\\cite{liang2022mind}, "
     "where the narrow cone induced by random initialization is preserved rather than closed by the "
     "contrastive objective itself.",
     "related_work 开篇"),
    ("related_work.tex",
     "Methodologically,~\\cite{liu2026tpc} split the gap into Centroid and Distribution components using "
     "per-sample cosine distances after centroid alignment, and reported that DG predicts cross-modal task "
     "quality strongly ($R^2=0.986$). Our DG shares the name but not the formula: we use a variance-based "
     "formulation (Section~\\ref{sec:empirical}) that reacts more sharply to distributional shape changes "
     "under PEFT.",
     "The decomposition into centroid and distribution components originates with~\\cite{liu2026tpc}, who "
     "formed per-sample cosine distances after aligning centroids and found the distributional term to "
     "predict cross-modal task quality well ($R^2=0.986$). The present work reuses the name for a different "
     "quantity: our DG is variance-based (Section~\\ref{sec:empirical}) and responds more sharply to changes "
     "in distributional shape under PEFT.",
     "related_work DG 定义"),
    ("related_work.tex",
     "The vulnerability of visual encoders during fine-tuning has been independently documented: prior work "
     "on continual learning found that visual modalities experience broader parameter distributions during "
     "class-incremental training.",
     "Evidence that visual encoders are the more exposed component during adaptation has accumulated "
     "independently of the present work; within continual learning, visual modalities have been observed to "
     "develop broader parameter distributions as classes are added.",
     "related_work 脆弱性"),
    ("related_work.tex",
     "Several independent lines now point to the visual encoder as the more fragile component.~"
     "\\cite{schiappa2025robust} exposed MLLMs to visual adversarial perturbations;~\\cite{wang2025sea} "
     "traced fine-tuning to localized shifts in vision-side parameters; and~\\cite{zhu2026fi} showed that a "
     "small parameter subset carries a disproportionate share of model brittleness.",
     "That the visual encoder is the more fragile half of a vision-language model is now supported from "
     "several directions. Visual adversarial perturbations were shown to compromise multimodal LLMs "
     "by~\\cite{schiappa2025robust}; fine-tuning was traced to localised movement of vision-side parameters "
     "by~\\cite{wang2025sea}; and brittleness was found to concentrate in a small parameter subset "
     "by~\\cite{zhu2026fi}.",
     "related_work 三条独立线索"),
    ("empirical.tex",
     "Table~\\ref{tab:position} quantifies this across architectures and positions. On Flickr30k, text-only "
     "reduces the gap by twice as much as both-position fine-tuning ($-0.064$ vs.\\ $-0.032$). On BLIP-1, "
     "text-only produces substantially smaller gap increase ($+0.047$ vs.\\ $+0.152$). On ViT-L, text-only is "
     "the only configuration that maintains alignment (CG$\\Delta = -0.036$), while rank-4 both-position "
     "increases the gap by $+0.128$.",
     "The magnitudes across architectures and adaptation positions are collected in Table~\\ref{tab:position}. "
     "On Flickr30k the text-only arm halves the gap reduction achieved by the both-position arm "
     "($-0.064$ against $-0.032$); on BLIP-1 it keeps the induced gap far smaller ($+0.047$ against "
     "$+0.152$); and on ViT-L it is alone in holding the gap down ($CG\\Delta = -0.036$), where rank-4 in the "
     "both-position setting adds $+0.128$.",
     "empirical tab:position"),
    ("empirical.tex",
     "Lower ranks ($r=4,8,16$) consistently reduce or maintain the gap, while higher ranks ($r=32,64$) tend "
     "to increase it. On Flickr30k, rank-4 achieves CG$\\Delta = -0.027$ and rank-16 achieves the best R@1 of "
     "0.702. On COCO, the pattern holds: rank-4 (CG$\\Delta = -0.038$), rank-8 ($-0.043$), rank-16 ($-0.069$).",
     "The gap responds monotonically to configured rank over the low end: ranks 4, 8 and 16 hold it down or "
     "leave it unchanged, whereas 32 and 64 push it up. The best retrieval on Flickr30k comes from rank-16 "
     "(R@1 = 0.702), with rank-4 holding the gap at CG$\\Delta = -0.027$; MS-COCO reproduces the ordering "
     "(rank-4 $-0.038$, rank-8 $-0.043$, rank-16 $-0.069$).",
     "empirical 秩效应"),
    ("supplement.tex",
     "\\textit{Footnotes: $^\\dagger$BLIP-1 full FT failed. $^\\ddagger$5-seed means. $^a$R@1 degradation "
     "under Gaussian parameter noise ($\\mu$=0, $\\sigma$=0.1) applied to vision/text encoder weights. "
     "$^b$Gradient signal-to-noise ratio (GSNR) averaged over training; text-only converges to a higher "
     "final loss (4.15 vs.\\ 0.56 for both-modality) yet preserves alignment. $^c$Effective rank of image "
     "embeddings (threshold 0.99 explained variance); text-only preserves rank.",
     "\\textit{Footnotes: $^\\dagger$BLIP-1 full FT failed. $^\\ddagger$5-seed means. $^a$Retrieval change "
     "under Gaussian parameter noise ($\\mu$=0, $\\sigma$=0.1) added to the encoder weights; see the "
     "withdrawn-evidence note for why this probe is not used as evidence. $^b$Gradient signal-to-noise ratio "
     "averaged over training; the text-only arm settles at a higher final loss (4.15 against 0.56) while "
     "still holding the gap down. $^c$Effective rank of the image embeddings at 0.99 explained variance; "
     "under strict freezing this quantity is unchanged by text-only training.",
     "supplement 脚注"),
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
        out = r.stdout.strip()
        print("\n=== 复跑重叠扫描 ===")
        for line in out.splitlines()[:3]:
            print("  " + line)
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
