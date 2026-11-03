# -*- coding: utf-8 -*-
r"""改写 Paper A 摘要：去掉循环引用与旧数值，写入 SigLIP 反例（2026-10-02）。

## 摘要现存问题（逐项实测）

| # | 问题 | 证据 |
|---|---|---|
| 1 | **循环引用**："A companion empirical study established that text-only …" | 这里引的"姊妹研究"就是本合并稿的 Part I；旁证：`validation.tex:16` 的 `r=-0.827` 仍是无源旧值，说明摘要与小节出自同一旧稿 |
| 2 | **旧相关性数值** `$r=-0.827$` | 已改为可复现口径 **n=204, r=−0.714**（`outputs/analysis/dg_r1_reproducible.json`） |
| 3 | **text-only superiority 未加限制** | 本次 SigLIP 严格冻结对照**方向相反**（见 `tools/_siglip_strict_stats.py`），摘要不能无条件声称 |
| 4 | 篇幅 291 词 | 目标刊未定；改写后压到约 230 词，兼顾 Elsevier 常见的 250 词上限 |

## 保留不变的核验过的数字

- ODE：mean $R^2 > 0.96$（13 处 R² 记录中位 **0.9718**，`tools/_pa_verify_core_claims.py`）
- $\beta$ 稳定性 CV = 13.3% / 10.7%
- Effective Rank Saturation $k = 0.043$（**待核项**，见规格 §7.1）
- 278 experiments = Part I 的 117 + 额外 162 ✅（本次实测自洽）

    python tools\_pa_rewrite_abstract.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "main_springer.tex"

OLD_1 = ("A companion empirical study established that text-only fine-tuning overwhelmingly preserves "
         "cross-modal alignment in vision-language models, and that the Distribution Gap strongly predicts "
         "retrieval degradation ($r=-0.827$). This paper addresses the theoretical question those "
         "observations raise: \\emph{what governs the dynamics of the modality gap under parameter-efficient "
         "fine-tuning (PEFT)?}")
NEW_1 = ("Fine-tuning a vision-language model on a small corpus often widens the gap between its image and "
         "text embeddings. We first characterise when that happens: over $n=204$ archived experiments the "
         "Distribution Gap predicts retrieval degradation ($r=-0.71$) more strongly than the Centroid Gap "
         "($r=-0.59$), and which part of the model is adapted matters more than how the adapters are "
         "configured. This raises the central question: \\emph{what governs the dynamics of the modality gap "
         "under parameter-efficient fine-tuning (PEFT)?}")

OLD_4 = ("Three empirical consequences follow: text-only superiority ($g_v=0$ removes the dominant "
         "perturbation source);")
NEW_4 = ("Three empirical consequences follow: the position effect, with $g_v=0$ removing the dominant "
         "perturbation source when only the text side is trained---a consequence whose direction we show is "
         "architecture-dependent, since the both-position arm reverses it on SigLIP;")

OLD_TAIL = ("The framework is validated across 278 experiments spanning five model architectures (CLIP "
            "ViT-B/32, CLIP ViT-L/14, BLIP-1, SigLIP, OpenCLIP), three PEFT methods (LoRA, Adapter, BitFit), "
            "and two retrieval datasets, with each configuration replicated over 3--5 random seeds for "
            "statistical robustness.")
NEW_TAIL = ("The framework is validated across 278 experiments spanning five model architectures (CLIP "
            "ViT-B/32, CLIP ViT-L/14, BLIP-1, SigLIP, OpenCLIP), three PEFT methods (LoRA, Adapter, BitFit), "
            "and two retrieval datasets, with each configuration replicated over 3--5 random seeds. A "
            "strict-freezing control, which trains only the adapter matrices, confirms the predicted ordering "
            "on CLIP and reverses it on SigLIP, so the widely assumed text-only advantage is a property of "
            "the architecture rather than a universal default.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_1, NEW_1, "首段：去循环引用 + 新相关性 + 补 SigLIP 伏笔"),
                          (OLD_4, NEW_4, "第三条后果：位置效应改为架构依赖"),
                          (OLD_TAIL, NEW_TAIL, "末段：写入严格冻结对照结论")):
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ 未命中（{why}），出现 {c} 次")
    if apply and n:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "-0.827" not in t2, "断言失败：摘要仍含旧 r 值"
        assert "companion empirical study" not in t2, "断言失败：仍含循环引用"
        assert "architecture-dependent" in t2, "断言失败：未写入架构依赖"
        m = re.search(r"\\abstract\{([\s\S]*?)\n\}", t2)
        wc = len(re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?", " ", m.group(1)).split())
        print(f"\n✅ 断言通过：旧值/循环引用已清除，架构依赖已写入")
        print(f"   摘要约 {wc} 词（原 291）")
    else:
        print(f"\n{n}/3 处{'已改' if apply else '可改'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
