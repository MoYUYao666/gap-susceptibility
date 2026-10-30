# -*- coding: utf-8 -*-
r"""修正 Paper A 里关于"两架构损失函数不同"的错误说法（2026-10-02）。

## 错在哪

正文（`validation.tex` 的 SigLIP 对照段）称：

> "We repeated that control on SigLIP, **whose pairwise sigmoid objective differs from CLIP's InfoNCE**"

以及

> "the two architectures differ in their **encoder and objective**"

**这是错的。** 读代码可证：`src/trainer.py:418-428` 的训练损失与模型无关——

    logit_scale = self.model.logit_scale.exp()
    logits_per_image = logit_scale * image_embeds @ text_embeds.T
    loss = (cross_entropy(logits_per_image) + cross_entropy(logits_per_text)) / 2

即**所有模型（含 SigLIP）微调时都用 InfoNCE**。SigLIP 只是**预训练**时用了 sigmoid；
微调阶段的损失与 CLIP 相同，故"目标不同"不成立。

## 为什么必须改

1. 该句把"损失函数"列为解释反向的候选，而**微调损失并不不同**——留着会误导审稿人；
2. 真正的混淆变量是**视觉骨干**（SigLIP patch-16 vs CLIP patch-32）与**预训练数据**。

## 改法

把"objective 不同"改为"预训练目标与视觉骨干不同"，并明确**微调损失两者相同**。

    python tools\_pa_fix_loss_claim.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()

    subs: list[tuple[str, str, str]] = []

    # 逐处定位（用短锚点，避免整段匹配过长）
    pats = [
        (r"the two architectures differ in their encoder and objective rather than in how they were trained",
         "the two architectures differ in their encoder and their pre-training rather than in how they were "
         "trained or in the loss they are fine-tuned with",
         r"differ in their encoder and objective"),
        (r"whose pairwise sigmoid objective differs from CLIP's\s*\n?\s*InfoNCE",
         "whose vision backbone and pre-training differ from CLIP's",
         r"pairwise sigmoid objective differs"),
    ]
    for pat, rep, tag in pats:
        m = re.search(pat, t)
        if m:
            subs.append((m.group(0), rep, tag))

    if not subs:
        print("  ⚠ 未命中任何待修表述；当前相关句：")
        for m in re.finditer(r"[^.]*objective[^.]*\.", t):
            print("     " + re.sub(r"\s+", " ", m.group(0))[:200])
        return 1

    for old, new, tag in subs:
        print(f"  ✅ 命中: …{tag}…")
        if apply:
            t = t.replace(old, new, 1)

    # 追加一句明确"微调损失相同"，避免读者继续误以为损失不同
    anchor = "differ in their encoder and their pre-training"
    add = (" (both are fine-tuned with the same InfoNCE objective used throughout this paper, so the "
           "difference lies in the encoders and how they were pre-trained, not in the training loss)")
    if apply and anchor in t and "same InfoNCE objective used throughout" not in t:
        t = t.replace(anchor, anchor + add, 1)
        print("  ✅ 追加澄清：微调损失两者相同")

    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "whose pairwise sigmoid objective differs" not in t2, "断言失败：旧说法仍在"
        assert "same InfoNCE objective used throughout" in t2, "断言失败：澄清未写入"
        # 确认没有别处再把损失当作差异
        bad = []
        for f in (REPO / "paper合" / "sections").glob("*.tex"):
            s = io.open(f, encoding="utf-8").read()
            if "sigmoid objective differs" in s:
                bad.append(f.name)
        assert not bad, f"仍有文件声称目标不同：{bad}"
        print("  ✅ 已改并断言通过")
    else:
        print(f"  {len(subs)} 处可改（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
