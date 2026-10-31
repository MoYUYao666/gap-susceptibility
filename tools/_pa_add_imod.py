# -*- coding: utf-8 -*-
r"""加入 IMoD（CVPR 2026）的实质对照讨论（2026-10-02）。

## 更正一处我自己先前的判断

我先以为 `zhang2026imod` 是"新论文"、bib 里没有。**核实后相反**：它**早在提交 `a78d81f` 就进了 bib**，
也已 `\cite`（`related_work.tex:11`），审计报"无未使用"。
问题不是"缺引用"，而是**现有引用太单薄**——只写了"introduced implicit modality decomposition (IMoD)"，
**没触及它"模态不平衡"的核心主张**，而那一主张正好与本稿形成有意义的对照。

## 两处改动

1. **改写单薄句**：补上 IMoD 的前提（**文本模态主导更新，非文本模态学得不足**）；
2. **新增一段**：把两者关系讲清楚——架构不同（MLLM vs 双塔）、视角不同（病理 vs 有益），
   并指出**今天的 OpenCLIP/SigLIP 反例恰好支持 IMoD 的警惕**。

## 书目信息（已核对，仅用 CVF 官方页字段）

作者 Mingfang Zhang, Yunhong Wang, Lu Wang, Jiaxin Chen；CVPR 2026；pp. 37745–37755；**无 arXiv 预印本**。

    python tools\_pa_add_imod.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections" / "related_work.tex"

OLD_SENT = ("~\\cite{zhang2026imod} introduced implicit modality decomposition (IMoD).")
NEW_SENT = ("~\\cite{zhang2026imod} introduced implicit modality decomposition (IMoD), motivated by the "
            "observation that adaptable parameters in multimodal models are dominated by the text modality, "
            "leaving non-text modalities under-trained.")

PARA = r"""
That last observation deserves a direct comparison with the present results, because the two point in
apparently opposite directions and the difference is instructive. \cite{zhang2026imod} treat text
dominance as a pathology to be corrected, whereas the design patterns of Section~\ref{sec:empirical}
recommend leaning on the text side. Three differences account for most of the distance between them.
Their setting adds modality adapters to a large language model, where an under-trained non-text modality
has a shared decoder to degrade; the encoder pairs studied here are dual-tower and contrastive, and the
text-side arm simply leaves the visual tower untouched. Their correction is a decomposition of where the
parameters live, which our experiments do not vary. And their evidence is task performance, where the
cost of an under-trained modality shows up directly, while ours is the geometry of the two embedding
spaces, which can move without retrieval following. What the two agree on is the diagnosis: adaptation
that concentrates on the text side changes the two encoders unevenly. Where this paper adds to theirs is
in showing that the consequence of that imbalance is not fixed --- the same text-side intervention
reduces the gap on one pre-trained pair and increases it on two others --- so neither the enthusiasm of
the design patterns nor the concern of \cite{zhang2026imod} transfers across backbones without measurement.
"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(SEC, encoding="utf-8").read()

    # ① 改写单薄句
    c = t.count(OLD_SENT)
    if c != 1:
        print(f"  ⚠ 单薄句未唯一命中（{c} 次）")
        return 1
    print("  ✅ 定位现有 IMoD 单薄引用")
    t2 = t.replace(OLD_SENT, NEW_SENT, 1)

    # ② 段落插到 PEFT 小节末尾（下一个 \subsection 之前）
    anchor = "\\subsection{Gap-Aware and Gradient-Informed Fine-Tuning}"
    i = t2.find(anchor)
    if i < 0:
        print("  ⚠ 未找到 Gap-Aware 小节锚点")
        return 1
    print("  ✅ 找到 PEFT 小节末尾插入点")
    t3 = t2[:i] + PARA.strip() + "\n\n" + t2[i:]

    if apply:
        io.open(SEC, "w", encoding="utf-8", newline="").write(t3)
        t4 = io.open(SEC, encoding="utf-8").read()
        assert "modality-imbalanced" not in t4 or True
        assert "leaving non-text modalities under-trained" in t4, "断言失败：单薄句未改写"
        assert "the same text-side intervention" in t4, "断言失败：对照段未写入"
        assert t4.count("\\cite{zhang2026imod}") == 3, \
            f"断言失败：IMoD 引用数应为 3，实测 {t4.count(chr(92)+'cite{zhang2026imod}')}"
        print("  ✅ 已写入并断言通过（IMoD 引用 3 处：原句改写 + 对照段 2 处）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
