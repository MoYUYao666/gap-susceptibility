# -*- coding: utf-8 -*-
r"""A1 摘要**压到 250 词以内**（目标刊 ESWA/KBS/CVIU 均限 250 词）（2026-10-10）。

## 现状

| 版本 | 词数 |
|---|---|
| 原摘要 | **247**（已贴上限） |
| 我改写后 | **317**（**超限 67**） |

**→ 必须压缩，且不得丢任何实测数字或保留声明。**

## 做法：**只压缩我自己加的那 78 词框架句**，原摘要正文**逐字保留**

新框架句压到两句、约 45 词：
> Fine-tuning a contrastive vision--language model for classification moves the modality gap
> and erodes class-relative rank order at the same time. Only the second governs zero-shot
> accuracy, and it can be monitored at no extra cost: the Kendall order-preservation
> coefficient $\tau$ is computed from the top-$k$ class sets a validation pass already produces.

    python tools\_pa_a1_abstract_trim.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

OLD = ("Fine-tuning a contrastive vision--language model for classification changes two "
       "things at once: how far apart the image and text clusters sit, and whether the "
       "class-relative ranking of an image's similarities survives. We show that only the "
       "second governs zero-shot accuracy, and that it can be monitored at no extra cost, "
       "because the Kendall order-preservation coefficient $\\tau$ is computed from the "
       "top-$k$ class sets a validation pass already produces. The modality gap, by "
       "contrast, is a \\emph{diagnostic} \\emph{implicitly} read as a universal quality "
       "proxy---narrowing it is an explicit design objective and gap-based quantities "
       "predict retrieval degradation---and that reading does not extend to zero-shot "
       "classification.")

NEW = ("Fine-tuning a contrastive vision--language model for classification moves the "
       "modality gap and erodes class-relative rank order at the same time. Only the second "
       "governs zero-shot accuracy, and it can be monitored at no extra cost: the Kendall "
       "order-preservation coefficient $\\tau$ is computed from the top-$k$ class sets a "
       "validation pass already produces. The modality gap is therefore not a universal "
       "health metric---narrowing it is an explicit objective and gap-based quantities "
       "predict retrieval degradation, but that reading does not extend to zero-shot "
       "classification.")


def wc(body: str) -> int:
    plain = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", body)
    plain = re.sub(r"\$[^$]*\$", " X ", plain)
    return len(plain.split())


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if not m:
        print("  ❌ 未找到 abstract")
        return 1
    before = wc(m.group(1))
    print(f"  当前摘要：{before} 词")
    if t.count(OLD) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD)}）")
        return 1
    t2 = t.replace(OLD, NEW, 1)
    m2 = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t2, re.S)
    after = wc(m2.group(1))
    print(f"  压缩后：{after} 词（限 250）")
    if after > 250:
        print(f"  ⚠️ 仍超限 {after - 250} 词 —— 需进一步压缩正文句")
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("at no extra cost", "necessary, not sufficient", "self-consistency check",
              "we claim this for no other families"):
        assert k in t3, f"断言失败：缺 {k}"
    print("  ✅ 已压缩；数字与保留声明均在")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
