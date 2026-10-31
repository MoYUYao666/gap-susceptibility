# -*- coding: utf-8 -*-
r"""落账：每周文献检索（2026-10-12）+ 工具教训（2026-10-12）。

    python tools\_docs_lit_weekly.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📚 2026-10-12 —— 每周文献检索（Paper A）：**7 天 1723 篇池、A 级 0 条、无直接竞争**；另记录两个检索工具的退化**
>
> ### 检索方法（**换了三次工具，前两次不可用**）
>
> | 工具 | 结果 | 判定 |
> |---|---|---|
> | OpenAlex `search=` 短语 | 返回太阳能电池 / 机场隧道 / 放射报告 / 眼底分类 | 🔴 **信噪比过低，不可用** |
> | arXiv `abs:"A" AND abs:"B"` | 多词字段查询**被当成 OR**（返回时间序列/ASR） | 🔴 **不可用** |
> | **arXiv `cat:cs.CV` + `cat:cs.LG` 分页抓取 → 本地正则过滤** | 池 **1723 篇**（覆盖 `2026-10-02 … 10-08`）| ✅ **可用** |
>
> **工具教训（须记住）**：arXiv API 的 `abs:` 字段**不支持多词 AND**；
> OpenAlex 的 `search=` 对长短语会退化成关键词 OR。**可靠做法是"抓全量 + 本地过滤"**
> （`tools/_lit_weekly4.py`，带 `outputs/analysis/lit_pool.json` 缓存，重跑不重抓）。
>
> ### 结果
>
> | 级别 | 判据 | 数量 |
> |---|---|---|
> | **A 级** | 摘要含 `modality gap` / `order preservation` **且**含任务词 | **0** |
> | B 级 | 含 `cross-modal align` / `kendall` 等 **且**含任务词 | 6 |
>
> ### B 级逐条核实（**已读摘要**，非凭标题；并查 `references.bib` 47 条）
>
> | arXiv | 是什么（据摘要） | 与本稿关系 | 行动 |
> |---|---|---|---|
> | `2610.09411v2` | *Shared Geometry As A Rosetta Stone*：**无需配对数据**的跨模态对齐（Wasserstein Procrustes + 粗几何初始化），并称"标准几何对齐指标能预测何时可行" | **可引用背景**（几何指标的可预测性；领域是模态间对齐，非 PEFT 内位置效应） | 仅记录 |
> | `2610.11113v1` | *DiscoVL*：VLM 的**解耦跨模态表示学习**，正交对抗正则 + 多分支低秩残差对齐器，防质心塌缩 | **可引用背景**（方法与"class-aligned 提升准确率"同向；非竞争） | 仅记录 |
> | `2610.11526v1` | *MSGAT*：脉冲神经网络做图文检索的图注意力 | **无关**（SNN 检索架构） | 忽略 |
> | `2610.09863v1` | *Global Average Precision*：全局 AP（gAP/gSAP），处理"跨查询相似度可比性" | **可引用背景**（度量设计；与 τ 无关） | 忽略 |
> | **`2610.09227v1`** | *Quantize by Drift*：用量化引起的**表示漂移**作为**无标签**信号，**排序**混合精度配置，与留出检索质量 macro Spearman **0.911** | ⚠️ **方法论同构**——同属"用无标签表示量排序配置"，但是**不同领域（量化）**，且**未引用本稿/团队**（OpenAlex：被引 0、references 0、本稿关键文献的被引列表里无它） | **仅记录**（可选：在 Related Work 加一句"同类思路在量化领域亦被采用"） |
> | `2610.06226v1` | *LeAVJEPA*：音视频自监督的极简架构 | **无关** | 忽略 |
>
> ### 三句总评
>
> 1. **无竞争性工作**：过去 7 天的 1723 篇 cs.CV/cs.LG 预印本里，**A 级 0 条**——
>    没有人同时在写"模态差 × 微调位置 × 秩序保持"。
> 2. **本稿最脆弱的主张未被挑战**：τ 的**有界性**已在自己稿里如实写明
>    （组内 +0.938、但停止决策价值未证明）；外部也没有出现反例。
> 3. **建议动作：不改稿**。`2610.09227` 可在投稿后作为"同类监控思路"的补充引用，
>    但**现在无需改动**（它是 2026-10-06 的预印本，且不构成竞争）。
>
> ### 附：`wan2026protect` 的 OpenAlex 记录有问题
>
> 按标题检索时命中的是另一篇（*One Modality to Forget Them All*），且 `wan2026protect`
> 在 OpenAlex 的 `cited_by_count = 0`、`n_references = 0`（元数据缺失）。
> **该条目的字段核实仍待操作者补**（与 2026-10-10 记录的"两条文献作者待补"同一事项）。
>
> **证据**：`outputs/analysis/lit_weekly_report.json`、`lit_verify.json`、
> `lit_2610_09227.json`、`lit_pool.json`（缓存：池 1723 条）；
> `tools/_lit_weekly4.py`、`_lit_verify.py`、`_lit_2610_09227.py`
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "每周文献检索（Paper A）" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("每周文献检索（Paper A）", "1723", "A 级 0 条", "2610.09227",
              "不支持多词 AND"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
