# -*- coding: utf-8 -*-
r"""修正结论段中已被 SigLIP 实验否定的普适处方（2026-10-02）。

## 为什么必须改

`conclusion.tex:11` 原文：

> "The central message is simple but now grounded in theory: **protect the visual encoder, fine-tune the
> text modality**, monitor the Distribution Gap. Our ODE explains why this strategy works---**and why it
> must**."

而严格冻结对照（同预算、同 seeds、同 rank）实测：

| 架构 | text_only | both | 结果 |
|---|---|---|---|
| CLIP | −0.0465 | −0.0258 | text-only 更降间隙（t=+10.0） |
| SigLIP | +0.0664 | **−0.0114** | **both 更降间隙（t=−52.7）** |

且 **both 在两架构上检索都更强**（CLIP 0.69 vs 0.62；SigLIP 0.62 vs 0.43）。
→ "fine-tune the text modality … **and why it must**" 是**已被反例否定**的普适处方。

另 `:5` 的 "establishing that text-only fine-tuning preserves cross-modal alignment" 与
"what damages cross-modal alignment is intervening on the visual side" 同样需加架构限定。

    python tools\_pa_fix_conclusion.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "conclusion.tex"

OLD_5 = ("establishing that text-only fine-tuning preserves cross-modal alignment, that the Distribution Gap "
         "predicts retrieval performance")
NEW_5 = ("establishing that adaptation at the text position preserves cross-modal alignment on the "
         "InfoNCE-based encoders studied (a direction we show reverses on SigLIP), that the Distribution Gap "
         "predicts retrieval performance")

OLD_11 = ("The central message is simple but now grounded in theory: protect the visual encoder, fine-tune the "
          "text modality, monitor the Distribution Gap. Our ODE explains why this strategy works---and why "
          "it must.")
NEW_11 = ("The practical message is narrower than a blanket recipe, and the ODE is what narrows it. Where the "
          "modality gap is the quantity of interest and the encoders are InfoNCE-trained, leaving the visual "
          "side alone and adapting the text side is the safer default, and the mechanism says why: with "
          "$g_v = 0$ the dominant perturbation term vanishes. That reasoning does not transfer automatically. "
          "On SigLIP the same control reverses the ordering, so the recipe has to be established per "
          "architecture rather than assumed. A second caution cuts across architectures: a smaller gap and "
          "better retrieval are not the same objective. Both-position adaptation retrieves better on CLIP and "
          "on SigLIP while reducing the gap more on only one of them, so monitoring the gap alone can point "
          "away from the configuration that retrieves best.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_5, NEW_5, "第一条：text-only 主张加架构限定"),
                          (OLD_11, NEW_11, "central message：去掉被否定的普适处方")):
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
        assert "and why it must" not in t2, "断言失败：普适处方仍在"
        assert "reverses on SigLIP" in t2 or "reverses the ordering" in t2, "断言失败：未写入架构依赖"
        print("  ✅ 已改并断言通过")
    else:
        print(f"  {n}/2 处{'已改' if apply else '可改'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
