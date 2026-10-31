# -*- coding: utf-8 -*-
r"""修正正文里关于两架构对照的错误 caveat，并把配对统计写实（2026-10-02）。

## 我的错误陈述

先前写入正文的是：

> "We note that the CLIP and SigLIP controls were run at different epoch budgets, so the reversal is an
> observation rather than an established consequence of the loss function"

**这句是错的。** 实测两者配置匹配（`tools/_crossarch_strict_stats.py`）：

| 项 | CLIP | SigLIP |
|---|---|---|
| max_samples | 5000 | 5000 |
| epochs | 10 | 10 |
| **LoRA rank / alpha** | **8 / 16** | **8 / 16** |
| gap_history 点数 | 7 | 7 |
| seeds | 42/123/456/789/1024 | 同一组 |
| batch_size | 128 | 64 |
| 可训参数（text_only） | 196,608 | 294,912 |

后两项是**编码器规模差异**（ViT-B/32 vs ViT-B/16），不是协议差异。

## 应写成的实测统计（配对，n=5）

| 架构 | text_only | both | 配对差 (both−text) | 配对 t |
|---|---|---|---|---|
| CLIP | −0.0465 ± 0.0030 | −0.0258 ± 0.0035 | **+0.0207**（sd 0.0046） | **+10.0** |
| SigLIP | +0.0664 ± 0.0060 | −0.0114 ± 0.0059 | **−0.0778**（sd 0.0033） | **−52.7** |

两架构**都显著、方向相反** → 架构依赖是**实测结论**。

**仍属推测的部分**：把方向相反归因于"InfoNCE vs pairwise sigmoid"——两架构同时差着编码器与嵌入
维度，本轮无法分离。改为如实表述。

    python tools\_pa_fix_xarch_caveat.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

OLD = ("Under the CLIP strict-freezing control of Section~\\ref{sec:empirical}, the text-only arm reduces the "
       "gap by more than the both-position arm ($-0.046 \\pm 0.003$ against $-0.026 \\pm 0.004$ over five "
       "seeds). We repeated that control on SigLIP, an architecture whose pairwise sigmoid objective differs "
       "from CLIP's InfoNCE, using identical budgets for both arms and five seeds each "
       "($294{,}912$ trainable parameters for text-only, with the vision side registering zero, against "
       "$589{,}824$ for both-position). \\textbf{The ordering reverses}: text-only \\emph{increases} the gap "
       "($+0.066 \\pm 0.006$) whereas both-position \\emph{reduces} it ($-0.011 \\pm 0.006$), a paired "
       "difference of $-0.078$ ($t = -52.7$, consistent in sign across all five seeds). The both-position arm "
       "also retrieves far better ($R@1 = 0.62$ against $0.43$). Two consequences follow. First, the "
       "text-only advantage is a property of the architecture rather than a universal default, so it should "
       "not be transferred to a new encoder without this control. Second, the two objectives come apart: "
       "both-position retrieves better on \\emph{both} architectures ($0.69$ against $0.62$ on CLIP) even "
       "though it reduces the gap more on only one of them, so minimising centroid or distribution gap is "
       "not a proxy for retrieval quality. We note that the CLIP and SigLIP controls were run at different "
       "epoch budgets, so the reversal is an observation rather than an established consequence of the loss "
       "function; the earlier non-frozen SigLIP runs are not used as evidence here, since they trained "
       "$1.89\\times10^{8}$ and $1.75\\times10^{8}$ parameters respectively and therefore did not isolate "
       "the adaptation site.")

NEW = ("Both controls below use the same recorded budget ($5000$ samples, $10$ epochs, LoRA rank $8$ with "
       "$\\alpha=16$) and the same five seeds, so the two architectures differ in their encoder and objective "
       "rather than in how they were trained. Under the CLIP strict-freezing control of "
       "Section~\\ref{sec:empirical}, the text-only arm reduces the gap by more than the both-position arm "
       "($-0.046 \\pm 0.003$ against $-0.026 \\pm 0.004$; paired difference $+0.021$, $t = +10.0$ over five "
       "seeds). We repeated that control on SigLIP, whose pairwise sigmoid objective differs from CLIP's "
       "InfoNCE ($294{,}912$ trainable parameters for text-only, with the vision side registering zero, "
       "against $589{,}824$ for both-position). \\textbf{The ordering reverses}: text-only \\emph{increases} "
       "the gap ($+0.066 \\pm 0.006$) whereas both-position \\emph{reduces} it ($-0.011 \\pm 0.006$), a paired "
       "difference of $-0.078$ ($t = -52.7$, consistent in sign across all five seeds). The both-position arm "
       "also retrieves far better on SigLIP ($R@1 = 0.62$ against $0.43$). Two consequences follow. First, "
       "the text-only advantage is a property of the architecture rather than a universal default, so it "
       "should not be transferred to a new encoder without this control. Second, the two objectives come "
       "apart: both-position retrieves better on \\emph{both} architectures ($0.69$ against $0.62$ on CLIP) "
       "even though it reduces the gap more on only one of them, so minimising centroid or distribution gap "
       "is not a proxy for retrieval quality. What the reversal is \\emph{not} yet pinned to is which "
       "architectural difference causes it: the two encoders differ in loss function, patch size and embedding "
       "width simultaneously, so we report the dependence and leave its attribution open. The earlier "
       "non-frozen SigLIP runs are not used as evidence here, since they trained $1.89\\times10^{8}$ and "
       "$1.75\\times10^{8}$ parameters respectively and therefore did not isolate the adaptation site.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(S / "validation.tex", encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未命中（出现 {c} 次）")
        return 1
    print("  ✅ 命中 validation 的 SigLIP 段")
    if apply:
        io.open(S / "validation.tex", "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(S / "validation.tex", encoding="utf-8").read()
        assert "different epoch budgets" not in t2, "断言失败：错误 caveat 仍在"
        assert "same recorded budget" in t2, "断言失败：未写入匹配预算"
        assert "t = +10.0" in t2 and "t = -52.7" in t2, "断言失败：配对统计未写全"
        print("  ✅ 已改并断言通过（错误 caveat 消除、CLIP 配对 t 值写入）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
