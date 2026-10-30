# -*- coding: utf-8 -*-
r"""更新 `文件地图.md`：A1 的投稿历程与目标刊（2026-10-10）。

**规则**：追加/就地更新，**不静默覆盖**旧条目；标注日期。

    python tools\_docs_filemap_a1.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FM = REPO / "文件地图.md"

OLD = ("- **A1**：投 PRL（PRLETTERS-D-26-01941）→ **2026-09-14 被拒** → "
       "修订后投 **Neurocomputing**")

NEW = ("- **A1**：投 PRL（PRLETTERS-D-26-01941）→ **2026-09-14 被拒** → "
       "修订后投 **Neurocomputing**（`NEUCOM-D-26-20952`）→ "
       "**2026-10-10 桌面拒稿**（编辑理由自相矛盾：既称\"不适合本刊读者\"，"
       "又称\"**falls within the aim and scope** … did not meet the significance level\"）→ "
       "**2026-10-10 操作者决定接受 ATS 转投、目标刊 = `Neural Networks`**"
       "（ISSN 0893-6080；免 APC；Guide 明载 APA 第 7 版）— "
       "**转投确认截止 `Nov 08 2026 23:59`**；"
       "合规改造已完成（摘要 245 词/关键词 5/highlights 5 条/**56 条文献转 APA**）；"
       "**待操作者点链接确认转投**")

ADD = """
> **📌 2026-10-10 状态更新（A1）**
>
> | 项 | 值 |
> |---|---|
> | 当前状态 | **ATS 转投待确认**（截止 `Nov 08 2026 23:59`） |
> | 目标刊 | **Neural Networks**（ISSN 0893-6080，Elsevier hybrid，**免 APC**） |
> | 编译 | **41 页 / 0 错误 / 0 未定义引用 / 0 Overfull** |
> | 标题 | *Order Preservation as a Zero-Overhead Monitor for Classification Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric* |
> | 摘要 | **245 词**（NN 限 250）｜关键词 **5**｜highlights **5 条** |
> | 参考文献 | **56 条，APA 第 7 版**（字母序；`\\citep`；`\\documentclass[review,authoryear]{elsarticle}`） |
> | 未决 | 2 条文献（`imod`/`hu2022lora`）作者无据可查 → 标 `Anon.`，**未编造** |
>
> **依据文件**：`期刊指南/_guide_neuralnetworks.txt`（操作者提供的 Guide PDF 提取）
> ｜**作者来源**：`outputs/analysis/a1_refs_openalex.json`（OpenAlex，逐条带 `method`/`similarity`）
"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(FM, encoding="utf-8", errors="replace").read()
    if "2026-10-10 操作者决定接受 ATS 转投" in t:
        print("  已更新，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ A1 行锚点未唯一命中（{t.count(OLD)}）")
        return 1
    t = t.replace(OLD, NEW, 1)
    # 在该节末尾追加状态块（找下一个 "## " 之前）
    i = t.find("## 二、最容易混的三组")
    if i > 0:
        t = t[:i] + ADD.strip() + "\n\n" + t[i:]
    if not apply:
        print("  （预演）")
        return 0
    io.open(FM, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(FM, encoding="utf-8", errors="replace").read()
    for k in ("ATS 转投待确认", "Neural Networks", "41 页", "245 词",
              "APA 第 7 版", "Nov 08 2026"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ 文件地图已更新（{len(t2.splitlines())} 行）：A1 行 + 状态块")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
