# -*- coding: utf-8 -*-
r"""加入每周文献检索发现的三条引用 + 一段辨析（2026-10-05）。

## 三条（字段均从官方页核实）

| key | 出处 | 核实方式 |
|---|---|---|
| `sharma2026readout` | arXiv:2609.36101, 2026-09-28 | arXiv abs 页（标题/作者/日期/摘要已读） |
| `yaras2026explaining` | arXiv:2412.07909（v2 2026-02-13） | arXiv abs 页（同上） |
| `chen2026dominance` | ACL 2026 long, pp. 36666–36678, **DOI 10.18653/v1/2026.acl-long.1699** | ACL Anthology 页 |

## 为什么要写辨析段

`yaras2026explaining` 与本稿**用同一理论工具（梯度流）**做间隙动力学，且称
"closing the modality gap leads to improved performance on image-text retrieval"——
与本稿"**降间隙 ≠ 提检索**"**表面冲突**。不辨析会显得漏读或回避。

**辨析的实质**（不是措辞回避）：
- `yaras` 研究**预训练**阶段间隙**如何产生**（不匹配数据对 + 可学习温度），其"关间隙改善检索"指
  **预训练时的干预**；
- 本稿研究**微调**阶段：位置选择如何改变间隙。**阶段不同**。
- `sharma` 在**下游任务**层面独立得出与本文同向的结论：干预效果依任务而异
  （降间隙利于零样本，移除间隙结构却损害检索）。
- **三者合起来支持一个更一般的说法**：不存在单一的"间隙目标"能同时优化所有检索设定。

## 纪律

- 不用 arXiv DOI（登记中），改用 `eprint` 字段；
- ACL 那条有正式 DOI，照录；
- 不在 bib 里写任何无法核实的字段。

    python tools\_pa_add_litsearch_20261005.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper合" / "references.bib"
SEC = REPO / "paper合" / "sections" / "related_work.tex"

BIB_ENTRIES = r"""
@article{sharma2026readout,
  title   = {One Geometry, Different Outcomes: Readout-Dependent Effects of the Modality Gap in
             Vision-Language Models},
  author  = {Sharma, Aditya and Saxena, Divya},
  journal = {arXiv preprint},
  eprint  = {2609.36101},
  archivePrefix = {arXiv},
  year    = {2026}
}

@article{yaras2026explaining,
  title   = {Explaining and Mitigating the Modality Gap in Contrastive Multimodal Learning},
  author  = {Yaras, Can and Chen, Siyi and Wang, Peng and Qu, Qing},
  journal = {arXiv preprint},
  eprint  = {2412.07909},
  archivePrefix = {arXiv},
  year    = {2026}
}

@inproceedings{chen2026dominance,
  title     = {The Dominance of Text Space: Unveiling the Asymmetric Nature of Cross-Modal Alignment
               in Large Language Models},
  author    = {Chen, Linqing and Zhong, Hanmeng and Wu, Wentao and Zhou, Peng},
  booktitle = {Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics
               (Volume 1: Long Papers)},
  pages     = {36666--36678},
  year      = {2026},
  doi       = {10.18653/v1/2026.acl-long.1699}
}
"""

# 插在 "Gap-Aware and Gradient-Informed Fine-Tuning" 小节末尾之前
PARA = r"""
Three recent accounts bear directly on how the gap should be treated, and taken together they narrow the
question rather than widen it. \cite{yaras2026explaining} analyse how the gap \emph{arises} during
contrastive pre-training through gradient-flow dynamics, locating the cause in mismatched pairs and a
learnable temperature, and report that closing the gap improves retrieval; their intervention is applied
while the encoders are being trained together, which is a different stage from the one studied here,
where the encoders are already fixed and only an adapter changes. \cite{sharma2026readout} work at the
downstream stage and on both CLIP and SigLIP, and find that interventions on the gap help some tasks and
hurt others: subtracting a fixed offset is equivalent to a bias term for zero-shot classification,
whereas projecting the gap direction out distorts retrieval rankings. \cite{chen2026dominance} arrive at a
related asymmetry from the language-model side, arguing that cross-modal alignment is an asymmetric
projection onto a rigid text manifold and that visual-side adjustment is what damages it. The present
results are consistent with all three and sharpen the practical conclusion: the gap is not an objective
that can be minimised on behalf of retrieval, because which adaptation site produces the smaller gap and
which produces the better retrieval need not be the same site at all.
"""


def main() -> int:
    apply = "--apply" in sys.argv
    bib = io.open(BIB, encoding="utf-8").read()
    sec = io.open(SEC, encoding="utf-8").read()

    have = [k for k in ("sharma2026readout", "yaras2026explaining", "chen2026dominance") if k in bib]
    if have:
        print(f"  bib 已含: {have}，跳过")
        return 0

    anchor = "\\subsection{Gap-Aware and Gradient-Informed Fine-Tuning}"
    if anchor not in sec:
        print("  ⚠ 未找到插入锚点")
        return 1
    print("  ✅ 找到插入点（PEFT 小节末尾）")

    if apply:
        io.open(BIB, "w", encoding="utf-8", newline="").write(bib.rstrip() + "\n" + BIB_ENTRIES)
        io.open(SEC, "w", encoding="utf-8", newline="").write(sec.replace(anchor, PARA.strip() + "\n\n" + anchor, 1))
        b2 = io.open(BIB, encoding="utf-8").read()
        s2 = io.open(SEC, encoding="utf-8").read()
        for k in ("sharma2026readout", "yaras2026explaining", "chen2026dominance"):
            assert k in b2, f"断言失败：bib 缺 {k}"
            assert k in s2, f"断言失败：正文未引用 {k}"
        assert "10.18653/v1/2026.acl-long.1699" in b2
        assert "2609.36101" in b2 and "2412.07909" in b2
        n = len([1 for l in b2.splitlines() if l.startswith("@")])
        print(f"  ✅ 已写入并断言通过 ｜ bib 现 {n} 条")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
