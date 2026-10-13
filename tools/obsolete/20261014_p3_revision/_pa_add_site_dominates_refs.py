# -*- coding: utf-8 -*-
r"""Paper A 侧解决"同一命题两处主张"：补文献定位 + 3 条书目（2026-10-07）。

## 背景与决定

- PRL 综述（`-02402`，在审）§3 首条 robust 结论 = **"site dominates allocation"**；
- Paper A 摘要 = **"which part of the model is adapted matters more than how its adapters are configured"**；
- **同一命题、两篇互不引用** → 有被读成自我重复的风险；
- **操作者决定：综述不改** → 只能从 Paper A 侧解决。

## 方案（**不引用在审稿件**）

Paper A **引用综述所依据的 3 篇已发表文献**，并把"位置 > 配置"定位为
「**单骨干场景前人已有观察 → 我们跨 7 个配置测到并证明它是架构（patch size）决定的，而非通用规律，并给出梯度流机制**」：

| 新增 | 作用 |
|---|---|
| 引用 `zhang2023adalora` / `wang2024loraga` / `zanella2024cliplora` | 承认文献基础（**避免"不看文献"与自我重复**） |
| 一句 framing | 把贡献**锐化**为"架构依赖 + 机制"，而非"我们发现位置重要" |

**书目取自综述（作者本人已核对过的条目），不从记忆编造。**

    python tools\_pa_add_site_dominates_refs.py [--apply]
"""
from __future__ import annotations

import ast
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper合" / "references.bib"
EMP = REPO / "paper合" / "sections" / "empirical.tex"

BIB_ADD = r"""
% ---- Site-vs-allocation evidence (cited so the position finding is placed against the literature) ----
@inproceedings{zhang2023adalora,
  title     = {{AdaLoRA}: Adaptive Budget Allocation for Parameter-Efficient Fine-Tuning},
  author    = {Zhang, Qingru and Chen, Minshuo and Bukharin, Alexander and Karampatziakis, Nikos},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2023}
}

@inproceedings{wang2024loraga,
  title     = {{LoRA-GA}: Low-Rank Adaptation with Gradient Approximation},
  author    = {Wang, Shaowen and Yu, Linxi and Li, Jian},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  year      = {2024}
}

@inproceedings{zanella2024cliplora,
  title     = {Low-Rank Few-Shot Adaptation of Vision-Language Models},
  author    = {Zanella, Maxime and Ben Ayed, Ismail},
  booktitle = {IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)},
  year      = {2024}
}
"""

ANCHOR = "\\subsection{Design Patterns}"

NEW_PARA = r"""\subsection{Placement Against Prior Work}

Individual studies have argued that the choice of adaptation site outweighs how a fixed budget is
divided within it in the low-data regime, and report gains from siting adaptation so that the
vision tower is left unchanged rather than from re-allocating rank among its modules
\cite{zhang2023adalora,wang2024loraga,zanella2024cliplora}. What those reports establish is that
the choice matters; they do not establish how far the resulting ordering generalises, because each
is measured on one backbone and one task corpus. We therefore treat the ordering as a hypothesis
rather than a premise and measure the same three arms on seven backbones under a protocol in which
the optimiser sees only the adapter matrices. The measurements above show that the ordering is a
property not of vision-language adaptation in general but of the patch size the encoder uses, and
Section~\ref{sec:theory} derives the mechanism that produces it.

"""


def main() -> int:
    apply = "--apply" in sys.argv
    bib = io.open(BIB, encoding="utf-8").read()
    emp = io.open(EMP, encoding="utf-8").read()

    n = 0
    if "zhang2023adalora" in bib:
        print("  · bib 已含新条目")
    else:
        bib2 = bib.rstrip() + "\n" + BIB_ADD
        n += 1
        print("  ✅ bib 将追加 3 条（AdaLoRA / LoRA-GA / CLIP-LoRA）")

    if ANCHOR not in emp:
        print(f"  ❌ 未找到锚点 {ANCHOR}")
        return 1
    if "Placement Against Prior Work" in emp:
        print("  · 段落已存在")
    else:
        n += 1
        print("  ✅ 将在 Design Patterns 前插入「Placement Against Prior Work」段")

    if not apply:
        print(f"\n  （预演，{n} 处改动；加 --apply 写入）")
        return 0
    if "zhang2023adalora" not in bib:
        io.open(BIB, "w", encoding="utf-8", newline="").write(bib2)
    if "Placement Against Prior Work" not in emp:
        io.open(EMP, "w", encoding="utf-8", newline="").write(emp.replace(ANCHOR, NEW_PARA + ANCHOR, 1))

    # 断言
    b2 = io.open(BIB, encoding="utf-8").read()
    e2 = io.open(EMP, encoding="utf-8").read()
    for k in ("zhang2023adalora", "wang2024loraga", "zanella2024cliplora"):
        assert f"@{k.split('20')[0]}" in b2 or k in b2, f"bib 缺 {k}"
    assert "Placement Against Prior Work" in e2
    assert r"\cite{zhang2023adalora,wang2024loraga,zanella2024cliplora}" in e2
    cnt = len(re.findall(r"^@", b2, re.M))
    print(f"\n  ✅ 已写入 ｜ bib 条目 {cnt} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
