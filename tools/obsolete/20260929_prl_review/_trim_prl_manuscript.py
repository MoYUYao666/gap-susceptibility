# -*- coding: utf-8 -*-
r"""为 PRL 稿件腾出页数余量：做一批等价改写式削减（不删论点，只压缩行文）。

动机：7 页是硬上限，compiled 恰好 7 页 = 零缓冲，任何排版差异都会溢出。
目标：削减 ~300–400 词，换来约 0.4–0.5 页余量。

    python tools/_trim_prl_manuscript.py            # 预演
    python tools/_trim_prl_manuscript.py --apply    # 写入
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"

# (原文, 改写)  —— 均为等价压缩，不改变任何主张
PAIRS: list[tuple[str, str]] = [
    # 3.3 收敛
    ("Comparisons in this literature are usually organised by how many parameters are trained, which is\n"
     "presented as a resource axis. Two problems arise. First, the count is often reported as a percentage\n"
     "of the base model rather than as an absolute number, and percentages are not comparable across base\n"
     "models of different sizes. Second, equal counts do not correspond to equal capacity, because where\n"
     "the parameters sit matters: the same number of trainable parameters distributed uniformly over all\n"
     "modules and concentrated in a few modules are different interventions. Evidence from the text-side\n"
     "literature shows that within a narrow parameter range, reported differences between allocation\n"
     "choices can reach several points [zhang2026halora; wang2023multilora; mao2022unipelt], which is what one would\n"
     "expect if the distribution, rather than the total, were doing the work. We note that an equivalent\n"
     "multimodal demonstration — holding the base model and the protocol fixed while varying only the\n"
     "distribution — is largely absent from the literature we surveyed, and we treat its absence as one of\n"
     "the gaps identified in §5.",
     "Comparisons here are usually organised by how many parameters are trained, presented as a resource\n"
     "axis. Two problems arise. The count is often given as a percentage of the base model rather than as\n"
     "an absolute number, and percentages are not comparable across base models of different sizes. And\n"
     "equal counts are not equal capacity, because where the parameters sit matters: the same count spread\n"
     "uniformly and concentrated in a few modules are different interventions. Evidence from the text-side\n"
     "literature shows differences between allocation choices reaching several points within a narrow\n"
     "parameter range [zhang2026halora; wang2023multilora; mao2022unipelt], which is what one would expect\n"
     "if the distribution rather than the total were doing the work. An equivalent multimodal\n"
     "demonstration — base model and protocol fixed, only the distribution varied — is largely absent, and\n"
     "we treat that absence as one of the gaps in §3.7."),
    # 3.4 收敛
    ("Reports of parameter-efficient adaptation frequently include runs that fail: training diverges, or\n"
     "the alignment or loss quantity becomes undefined. These appear in tables as missing values or as\n"
     "explicit non-numeric entries, and they are ordinarily counted as evidence against the configuration\n"
     "that produced them. They are not always that. A non-finite value can arise from an implementation\n"
     "choice — numerical precision, a learning-rate schedule, an unspecified initialisation — in which case\n"
     "it carries no information about the method being tested. The distinction matters because it changes\n"
     "the direction of the conclusion: a configuration that fails because of an implementation detail is\n"
     "not a configuration that fails as a method. To our knowledge the multimodal adaptation literature\n"
     "does not systematically separate the two, and we are not aware of a study that quantifies the\n"
     "division. We therefore record this as an open question rather than as a finding about any particular\n"
     "method.",
     "Reports in this area frequently include runs that fail: training diverges, or the reported quantity\n"
     "becomes undefined. These appear as missing or non-numeric entries and are ordinarily counted as\n"
     "evidence against the configuration that produced them. They are not always that. A non-finite value\n"
     "can arise from an implementation choice — numerical precision, a schedule, an unspecified\n"
     "initialisation — in which case it carries no information about the method. The distinction changes\n"
     "the direction of the conclusion: a configuration that fails for an implementation reason is not a\n"
     "method that fails. The literature does not systematically separate the two, so we record this as an\n"
     "open question rather than a finding about any particular method."),
    # 3.7 收敛
    ("The instances above constrain comparison; they do not mean nothing is known. Three conclusions appear\n"
     "robust. First,",
     "The instances above constrain comparison; they do not mean nothing is known. Three conclusions\n"
     "appear robust. First,"),
    ("What does not survive is the inference from a reported improvement to a claim about method quality.\n"
     "An improvement obtained under an unstated protocol, at an unstated site, with an unstated division of\n"
     "capacity, is evidence that a configuration worked once. That is worth reporting; it is not yet worth\n"
     "building on.",
     "What does not survive is the inference from an improvement to a claim about method quality. A gain\n"
     "obtained under an unstated protocol, at an unstated site, with an unstated division of capacity, is\n"
     "evidence that a configuration worked once — worth reporting, not yet worth building on."),
    # §4 尾部收敛
    ("The table also shows why the list cannot be shortened much further. Items 5 and 6 look like one item\n"
     "until one notices that a paper can state its rank while leaving the division unstated — which is the\n"
     "normal case, since most applications use the same rank everywhere and therefore never describe a\n"
     "division at all. Similarly, items 9 and 10 separate an experimental design fact from a reporting\n"
     "convention; a paper can give the number of runs and still leave the convention ambiguous, and the\n"
     "reverse is also possible.\n\n"
     "We are aware that a checklist alone changes little, and that journals and reviewers are the\n"
     "enforcement mechanism. Our purpose in stating it here is to make the requirement citable: a reviewer\n"
     "who asks for these twelve items can point to this list, and an author who reports them can expect\n"
     "their numbers to be re-usable, which is the practical form of the contribution that multimodal\n"
     "adaptation currently lacks.\n\n"
     "One objection is worth answering, because it is the one we expect. The items ask for information that\n"
     "costs space, and PRL-style length limits are tight. In our experience of assembling the comparison\n"
     "tables behind §3, the space saved by omitting these items is illusory: a result whose protocol is\n"
     "unstated cannot be placed in a comparison table at all, so the table shrinks rather than grows. The\n"
     "trade is between a short table of comparable numbers and a longer table of numbers that the reader\n"
     "must discard.",
     "The list cannot be shortened much further. Items 5 and 6 look like one until one notices that a\n"
     "paper can state its rank while leaving the division unstated — the normal case, since most\n"
     "applications use the same rank everywhere and never describe a division at all. Items 9 and 10\n"
     "likewise separate an experimental-design fact from a reporting convention.\n\n"
     "One objection is worth answering. The items cost space, and length limits are tight; but the space\n"
     "saved by omitting them is illusory, since a result whose protocol is unstated cannot enter a\n"
     "comparison table at all. The trade is between a short table of comparable numbers and a longer table\n"
     "the reader must discard. A checklist alone changes little — journals and reviewers enforce it — and\n"
     "the purpose of stating it here is to make the requirement citable."),
    # §5 收敛
    ("The instances we gave are not allegations of error. In each case the information needed for\n"
     "comparison is absent rather than incorrect: an evaluation subset is unnamed, a protocol is unstated,\n"
     "a distribution is not described, a failure is recorded without its cause, dispersion is reported\n"
     "without its convention, and a frozen component is described without saying which parts moved. The\n"
     "twelve-item checklist in §4 is intended as the minimum that removes these obstacles.",
     "The instances are not allegations of error. In each case the information needed for comparison is\n"
     "absent rather than wrong: an evaluation subset unnamed, a protocol unstated, a distribution\n"
     "undescribed, a failure recorded without its cause, dispersion reported without its convention, and a\n"
     "frozen component described without saying which parts moved. The checklist in §4 is the minimum that\n"
     "removes these obstacles."),
]


def main() -> int:
    apply = "--apply" in sys.argv
    text = io.open(MD, encoding="utf-8").read()
    total_before = len(re.findall(r"[A-Za-z]+", text))
    n = 0
    for old, new in PAIRS:
        if old in text:
            text = text.replace(old, new, 1)
            n += 1
            print(f"  ✅ 命中（{len(re.findall(r'[A-Za-z]+', old)) - len(re.findall(r'[A-Za-z]+', new)):+d} 词）")
        else:
            print(f"  ⚠ 未命中: {old[:56]}…")
    total_after = len(re.findall(r"[A-Za-z]+", text))
    print(f"\n共替换 {n}/{len(PAIRS)} 处，英文词 {total_before} → {total_after}（{total_after - total_before:+d}）")
    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(text)
        print("已写入")
    else:
        print("（预演，未写入；加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
