# -*- coding: utf-8 -*-
r"""把「候选刊近年实际刊载内容」实证核查写入决策文档（2026-10-07）。

    python tools\_docs_venue_content_evidence.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "docs" / "PAPERA_VENUE_DECISION.md"

SEC = r"""

---

## 五、实证明查：候选刊**近年实际刊载内容**（2026-10-07 追加）

**动机**：Guide 只给"研究领域"（CVIU 列有 "Data structures and representations" 与 "Theory"），
**不能回答"该刊实际收什么"**——而这才决定 desk-reject 风险。故用 **OpenAlex API**（公开、可复核）实查。

### 四轮核查，方法逐轮修正

| 轮次 | 脚本 | 方法 | 结果 |
|---|---|---|---|
| 1 | `_venue_content_survey.py` | 关键词分类，每刊 200 篇（2024 起） | ⚠️ **假阳性严重**：`rank` 命中 "Rank Graduation Box"、`convergence` 命中 "Hiking Optimization Algorithm"、`embedding` 命中 "knowledge graph embedding"。**且 CVIU 的"表征类"样本全是视觉任务**（Video Anomaly Recognition、light-field super-resolution、RGB-D semantic segmentation）——只是**碰巧提到 embedding** |
| 2 | `_venue_topic_probe.py` | 用**本文主题词**检索 | ✅ CVIU：`parameter-efficient fine-tuning` **48**、`vision-language alignment` **28**、`LoRA` **11** → **有大量同类技术先例**。但返回标题**全是"方法应用到具体视觉任务"** |
| 3 | `_venue_analysis_probe.py` | 区分「**分析类**」vs「任务类」措辞 | ⚠️ **返回标题与检索词不对题**（如查 `understanding representation collapse` 返回 *"Escaping the big data paradigm in self-supervised representation learning"*）→ **OpenAlex 为宽泛 OR 匹配，计数被夸大** |
| 4 | 目视逐条核对返回标题 | —— | **无一篇是"分析优先"的论文** |

### 决定性观察

CVIU / ESWA / KBS **都在发 VLM + PEFT 的工作**，但形态**一致**：

> **"把方法应用到具体任务"** —— semantic segmentation、medical image segmentation、
> anomaly detection、depth human parsing、video inpainting …

**没有观察到任何一篇"以分析表征几何 / 训练动态本身为目的"的论文。**

→ 本文（**分析优先 + 理论**：383 实验、5 架构、3 种 PEFT 方法）与这 5 个刊的
**实际刊载形态不匹配**。**这是 scope 风险的真实来源，且用检索无法消除。**

### ⚠️ 核查的**局限**（诚实标注，不夸大结论）

1. OpenAlex 为**宽泛匹配**，**计数不可当作精确篇数**（已由返回标题证实不对题）；
2. 未取得**完整目录**（ScienceDirect 返回 **403**）→ 样本非全体，**不能断言"该刊从不收"**；
3. 分类规则由我编写，**已目视发现假阳性**，故**采信"返回标题"而非"计数"**；
4. 仅在英文**标题/摘要**层面检索，**未逐篇读正文**，故"是否分析优先"依标题判断，可能有偏差。

→ **结论强度：方向可信（四轮同向），但不是穷尽证明。**

### 数据落盘（可复核）

- `outputs/analysis/venue_content_survey.json`
- `outputs/analysis/venue_topic_probe.json`
- `outputs/analysis/venue_analysis_probe.json`

### 对结论的影响

**先前推荐 ESWA（首选）/ CVIU（次选），依据是 Guide 的篇幅与流程条件——那些条件仍然成立**
（ESWA/CVIU 无篇幅上限、CVIU 单盲且首轮 3.7 月、ESWA 首轮 5.4 月）。

**但本次核查表明：scope 风险对两刊同样实在，且不因换刊而消除。**

**→ 决策实为三选一**：

| 选项 | 做法 | 风险 |
|---|---|---|
| **1. 改包装 → ESWA** | 把表征分析落到**可复用的设计准则/实用指南**，命中其 *"design, development, testing, implementation … practical guidelines"* 措辞 | 需重写引言的 framing；仍可能被判非系统类 |
| **2. 改包装 → CVIU** | 把**视觉侧**结论前置，弱化文本/NLP 侧；强调 "Data structures and representations" | 需重写 framing；仍可能被判非图像理解 |
| **3. 另找 scope 真正对的刊** | 当前 5 个候选**均非"分析型"定位** | 需重新取证（且须复核免 APC 与拒稿史） |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "近年实际刊载内容" in t:
        print("  已写入，跳过")
        return 0
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t.rstrip() + SEC)
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("近年实际刊载内容", "宽泛 OR 匹配", "无一篇", "改包装", "局限"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ 已写入（{len(t2.splitlines())} 行）")

    # HANDOFF
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = r"""> **🔬 2026-10-07 —— 实证明查候选刊「近年实际刊载内容」：**scope 风险对 5 刊同样实在****
>
> **交付件**：`docs/PAPERA_VENUE_DECISION.md` §五（含四轮方法与我自己的错误修正）。
>
> ### 四轮核查（方法逐轮修正，**前三轮都有缺陷，已如实记录**）
>
> | 轮 | 方法 | 结果 |
> |---|---|---|
> | 1 | 关键词分类 200 篇/刊 | ⚠️ **假阳性严重**（`rank`→"Rank Graduation Box"、`convergence`→优化算法）；CVIU 的"表征类"样本**全是视觉任务** |
> | 2 | 本文主题词检索 | ✅ CVIU `parameter-efficient fine-tuning` **48**、`vision-language alignment` **28**、`LoRA` **11** → **同类技术先例很多** |
> | 3 | 「分析类 vs 任务类」措辞 | ⚠️ **返回标题与检索词不对题** → OpenAlex 是**宽泛 OR 匹配，计数夸大** |
> | 4 | 目视逐条核对 | **无一篇是"分析优先"的论文** |
>
> ### 决定性观察
>
> CVIU/ESWA/KBS **都在发 VLM+PEFT**，但形态**一致**：**"把方法应用到具体任务"**
> （segmentation / medical segmentation / anomaly detection / depth parsing …）。
> **没有一篇是"以分析表征几何本身为目的"的论文。**
>
> → 本文（**分析优先 + 理论**）与此形态**不匹配**。**scope 风险真实存在，检索无法消除。**
>
> ### ⚠️ 局限（不夸大）
>
> OpenAlex **宽泛匹配**（计数≠精确篇数）｜ ScienceDirect **403** 未取全目录（**不能断言"从不收"**）｜
> 分类规则**我写的且已发现假阳性**（故**采信返回标题而非计数**）｜ 仅标题/摘要层面，**未读正文**。
> **→ 方向可信（四轮同向），但非穷尽证明。**
>
> ### 对决策的影响
>
> 先前推荐 ESWA/CVIU 的**篇幅与流程依据仍成立**（无篇幅上限；CVIU 单盲、首轮 3.7 月；ESWA 首轮 5.4 月），
> **但 scope 风险对两刊同样实在**。**→ 实为三选一**：① **改包装**投 ESWA（落到"设计准则/实用指南"）；
> ② **改包装**投 CVIU（视觉侧前置）；③ **另找 scope 真正对的刊**（当前 5 个候选均非分析型定位）。
> 详见 `docs/PAPERA_VENUE_DECISION.md` §五 末表。
"""
    if "实证明查候选刊" not in h:
        anchor = "> **🎯 2026-10-07 —— A-1 目标刊对照完成"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("无一篇是", "宽泛 OR 匹配", "改包装", "PAPERA_VENUE_DECISION.md"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
