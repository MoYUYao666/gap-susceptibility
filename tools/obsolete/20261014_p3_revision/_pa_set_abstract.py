# -*- coding: utf-8 -*-
r"""写入 Paper A 的定稿摘要（≤250 词）。

先前三次尝试均因超 250 词而未写入（脚本的闸门正确生效）。
本版一次性给出达标文本，并在写入前断言词数。

    python tools\_pa_set_abstract.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "main_springer.tex"

NEW = r"""\abstract{
Fine-tuning a vision-language model on a small corpus often widens the gap between its image and text
embeddings. We first characterise when. Across $n=204$ archived experiments the Distribution Gap predicts
retrieval degradation ($r=-0.71$) more strongly than the Centroid Gap ($r=-0.59$), and which part of the
model is adapted matters more than how its adapters are configured.

We then derive \emph{Gap Susceptibility} from gradient flow. With the alignment energy as a state
variable, the rate of gap change is the projection of the task gradient onto the alignment gradient,
splitting into sensitivity and directional-coupling terms.

The resulting first-order ODE has a perturbation force that follows from that coupling, and a restoring
coefficient that is stable within PEFT while its full-fine-tuning estimate varies with batch. The ODE
predicts the full gap trajectory at mean $R^2 > 0.96$ across all tested LoRA configurations, against
$0.00$ for a constant baseline and $0.946$ for a linear one.

Three consequences follow: adaptation position, since removing the visual gradient term removes the
dominant perturbation source; a protective bound for LoRA across ranks; and a task gradient whose
effective dimension is set by task structure rather than configured rank. Validation spans 278
experiments over five architectures, three PEFT methods and two retrieval datasets. A strict-freezing
control training only adapter matrices confirms the predicted ordering on CLIP and reverses it on
SigLIP: the text-only advantage is a property of the architecture, not a universal default.
}"""


def wc(s: str) -> int:
    body = re.search(r"\\abstract\{([\s\S]*?)\n\}", s).group(1)
    plain = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?", " ", body)
    plain = re.sub(r"[$\\{}]", "", plain)
    return len(plain.split())


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    m = re.search(r"\\abstract\{[\s\S]*?\n\}", t)
    if not m:
        print("  ⚠ 未找到摘要")
        return 1
    print("  旧 %d 词 → 新 %d 词" % (wc(m.group(0)), wc(NEW)))
    n = wc(NEW)
    if n > 250:
        print("  ⚠ 超 250，拒绝写入")
        return 1
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(m.group(0), NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert wc(re.search(r"\\abstract\{[\s\S]*?\n\}", t2).group(0)) == n
        assert "-0.827" not in t2 and "companion empirical study" not in t2
        assert "not a universal default" in t2
        print(f"  ✅ 已写入（{n} 词 ≤ 250）并断言通过")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
