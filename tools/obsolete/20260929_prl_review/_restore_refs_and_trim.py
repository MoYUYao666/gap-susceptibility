# -*- coding: utf-8 -*-
r"""按"同类稿件基准"补足引用（35 → ~47 条），同时压缩正文以守住 7 页硬上限。

依据：`tools/_benchmark_prl_reviews.py` 实测 PRL 已发表综述类文章
      参考文献 **中位 55、四分位 37–59**；本文原为 35 条（低于下四分位）。

策略：把此前为让路而删掉的**实质性引用**补回（它们提升 §2 方法学覆盖与 §3 评测证据），
      同时压缩正文若干处，使总页数仍 ≤ 7。

    python tools/_restore_refs_and_trim.py            # 预演
    python tools/_restore_refs_and_trim.py --apply
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"

# (原文, 替换) —— 左列为当前稿件中的片段（允许跨行，用正则）
EDITS: list[tuple[str, str]] = [
    # 1) §1 综述定位：恢复视觉侧综述（与语言侧并列，符合"覆盖两侧"的写法）
    (r"two cover the language and vision settings respectively \[xu2026peftsurvey\]",
     "two cover the language [xu2026peftsurvey] and vision [xin2024vpeftsurvey] settings, and others "
     "survey efficiency more broadly [jin2024efficientmllm; shao2025tokencompression;\nlialin2023scalingdown]"),
    # 2) §2.1 视觉侧：恢复 Convpass / SAFE
    (r"\[chen2022adaptformer\] all modify how images are represented",
     "[chen2022adaptformer; jie2022convpass; he2023safe] all modify how images are\nrepresented"),
    # 3) §2.2 提示族：恢复四篇
    (r"adding trainable vectors rather\nthan weight updates \[li2021prefixtuning; lester2021prompttuning\]",
     "adding trainable vectors\nrather than weight updates [li2021prefixtuning; lester2021prompttuning; khattak2023maple;\nqiu2024progressive]"),
    # 4) §2.2 量化：恢复 QLoRA（预算由"秩 + 精度"共同构成，这是分配轴的一部分）
    (r"\[dettmers2023qlora\b",
     "[dettmers2023qlora"),
    # 5) §3.2 评测协议：恢复 MME 与评测批判两篇
    (r"\[liu2025mmbench\]\. Contamination between",
     "[liu2025mmbench; fu2025mme]. Contamination between"),
    # 6) §3.7 第三条：恢复统一框架（UniPELT）作为"混合目标"代表
    (r"\[belanec2026peftbench\]\.",
     "[belanec2026peftbench; mao2022unipelt]."),
]

# 同步瘦身（等价改写，抵消新增引用的行数）
TRIMS: list[tuple[str, str]] = [
    (r"This critical review argues that the framing obscures the\nactual structure of the problem, which consists of two decisions that are orthogonal and usually\nconflated\.",
     "This critical review argues that the framing obscures the problem's actual structure: two decisions,\northogonal and usually conflated."),
    (r"Two points about scope and method, stated at the outset because they bound what follows\. The review\ncovers multimodal and vision-language adaptation rather than text-only parameter-efficient\nfine-tuning, for which authoritative reviews exist \[xu2026peftsurvey\]\. And it is an argumentative review rather than a systematic one: the instances\nin §3 are individual cases chosen because each is checkable against its source, not a sample from\nwhich frequencies can be estimated\. Where a claim rests on the absence of a statement in a source\nrather than on a positive claim, the text says so\. A reader wanting a catalogue of methods should\nconsult the surveys cited above; the purpose here is to establish what those catalogues can currently\nbe used to conclude\.",
     "Two points bound what follows. The review covers multimodal and vision-language adaptation, not\ntext-only parameter-efficient fine-tuning, for which authoritative reviews exist [xu2026peftsurvey].\nAnd it is argumentative rather than systematic: the instances in §3 are individual cases chosen\nbecause each is checkable against its source, not a sample from which frequencies can be estimated.\nA reader wanting a catalogue of methods should consult the surveys cited above; the purpose here is\nto establish what those catalogues can be used to conclude."),
    (r"its modification cannot destroy representations the encoder produced, and training it alone has been\nreported as sufficient \[iskandar2026projector\]",
     "it cannot destroy representations the encoder produced, and training it alone has been reported as\nsufficient [iskandar2026projector]"),
    (r"The manuscript would be submitted as a survey article within the stated limits: about 45 pages and\napproximately 150 references",
     "about 45 pages and approximately 150 references"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(MD, encoding="utf-8").read()
    before = len(re.findall(r"\[([a-z][a-z0-9_]*\d[a-z0-9_]*)(?:[;,]\s*[a-z][a-z0-9_]*\d[a-z0-9_]*)*\]", t))

    n_add = 0
    for pat, rep in EDITS:
        t2, k = re.subn(pat, rep.replace("\\", "\\\\"), t, count=1)
        if k:
            t = t2
            n_add += 1
        else:
            print(f"  ⚠ 补引用未命中: {pat[:52]}…")

    n_trim = 0
    for pat, rep in TRIMS:
        t2, k = re.subn(pat, rep, t, count=1)
        if k:
            t = t2
            n_trim += 1
        else:
            print(f"  ⚠ 瘦身未命中: {pat[:52]}…")

    # 统计唯一 key
    keys = set()
    for m in re.finditer(r"\[([^\]\[]+)\]", t):
        inner = m.group(1)
        if "://" in inner:
            continue
        for part in re.split(r"[;,]", inner):
            k = part.strip()
            if re.match(r"^[a-z][a-z0-9_]*\d[a-z0-9_]*$", k):
                keys.add(k)
    print(f"\n补引用命中 {n_add}/{len(EDITS)} ｜ 瘦身命中 {n_trim}/{len(TRIMS)}")
    print(f"唯一引用 key: {len(keys)} 条")
    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("已写入")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
