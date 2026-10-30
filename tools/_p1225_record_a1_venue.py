# -*- coding: utf-8 -*-
r"""Record the A1 venue re-selection after the Neural Networks desk rejection.

    python tools/_p1225_record_a1_venue.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VENUE = REPO / "docs" / "A1_VENUE_DECISION.md"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

SECTION = """

---

## 十二、2026-10-18 重选：**首选 TMLR**（Neural Networks 桌面拒稿后）

### 12.1 为什么要换评估模型，而不只是换刊名

A1 的判死模式已经很清楚：

| 时间 | 期刊 | 结果 | 理由 |
|---|---|---|---|
| 2026-09-14 | PRL (`PRLETTERS-D-26-01941`) | 拒（有外审）| 见当时意见 |
| 2026-10-10 | Neurocomputing (`NEUCOM-D-26-20952`) | **桌面拒**（自相矛盾：既称"不适合读者"又称"within the aim and scope…did not meet significance"）|
| 2026-10-18 | Neural Networks (`NEUNET-D-26-09426`) | **桌面拒，未送审** | AE 原话："The technical novelty on neural networks is marginal." |

三次都不是数据/方法错误，而是**"新颖性/显著性"这一道编辑级门槛**。因此这次换刊的第一原则不是影响力，而是：
**目标刊的编辑流程里不能存在"单方面以新颖性桌面退稿"的机制**，且其评审标准要与本文的实际贡献（严谨的对照实验 + 可识别性论证 + 量化边界）对齐。

### 12.2 首选：**TMLR**（Transactions on Machine Learning Research）

**官方接受标准原文**（`jmlr.org/tmlr/acceptance-criteria.html`，2026-10-18 抓取）：

> "Crucially, it should not be used as a reason to reject work that isn't considered 'significant' or 'impactful'…
> Nor should it form the basis for rejecting work on a method considered **not 'novel enough', as novelty of the studied
> method is not a necessary criterion for acceptance in TMLR**. We explicitly avoid these terms ('significant',
> 'impactful', 'novel'), and focus instead on the notion of 'interest'."

而第一标准是：

> "Are the claims made in the submission supported by accurate and convincing evidence? This is the most important criterion."

⇒ **这正好把 A1 的最大风险（新颖性判断）从评审标准里删掉**，而把 A1 的最强项（证据强度：匹配 gap 控制、200 方向控制、
三骨干复现、量化边界、可复现归档）放在第一判据上。

**流程特征（同为官方页，2026-10-18 抓取）**：
- **双盲评审、投稿件必须匿名**（作者信息、致谢、自引措辞都需处理）；
- **不限长度**（"Submissions may be any length"，但过长会拖慢评审）；
- 必须用 **TMLR LaTeX 样式**；附录可放证明；可附 ≤100 MB 补充材料；
- **CC BY 4.0**；投稿后用 OpenReview 进行**开放式 rebuttal/讨论/修订**——没有"一票桌面退稿"环节；
- 作者指南**未提及任何费用**（无 APC）。

### 12.3 次选与兜底

| 顺位 | 期刊 | 适配理由 | 风险/待核 |
|---|---|---|---|
| **2** | **Pattern Analysis and Applications**（Springer）| 接受实证/分析型长文；分区适中 | **必须先核 Guide 的字数/页数政策**（IVC 的教训：不核政策就选刊等于白做）|
| **3** | Machine Vision and Applications / The Visual Computer（Springer）| 门槛较低、可容长文 | 评审仍可能按"新颖性"打分，桌面拒风险高于 TMLR |
| **4** | IEEE Access | 审稿快、接受扎实实证 | **有 APC**（约 2,000 USD 量级，需按当期费率核）；声望低于前两者 |
| ❌ | **IVC** | —— | **字数上限 4,500–7,500**，本稿 ~14k–17.7k 词，结构性不兼容（2026-09-15 已核）|
| ❌ | Neurocomputing / Neural Networks / Pattern Recognition / TNNLS / PRL | —— | 前两者已桌面拒；PR 拒过 P1；TNNLS 拒过 P3；PRL 已有 Commentary 在审 |

### 12.4 若选 TMLR：改造清单（估计 1 个工作日）

1. **模板**：elsarticle → `tmlr.sty`（官方 stylefile），重排 45 页；过长内容移入 Appendix；
2. **匿名化**：删作者块/单位/邮箱/致谢；`\\cite{wan2026protect}` 等自引改为第三人称转述；GitHub/Zenodo 链接改为匿名仓库
   （或"available in the supplementary material"）；
3. **附录**：非充分性命题的证明（形式化 top-1 只依赖行序）、边界定律的推导细节；
4. **补充材料**：归档 JSON + 复现脚本（匿名化）；
5. **Broader impact**：若无显著危害风险可不写；本文不涉及，建议不写或一句"no foreseeable societal risk"；
6. **摘要**：TMLR 无硬字数限制，现 285 词可用；但建议压到 ~230–250 词以利阅读。

### 12.5 推荐结论

**投 TMLR。** 理由不是"更容易"，而是**评估维度与本文贡献对齐**：它明确不看新颖性、只看证据是否支持主张，
并且没有编辑桌面退稿这一关。备选按 12.3 的顺位轮换，但每次换刊前**先核字数/页数政策**。
"""

ENT = """> **📮 2026-10-18 14:10 —— A1 换刊决策：首选 TMLR（Neural Networks 桌面拒后）**
>
> A1 三次被拒都不是数据/方法问题，而是**编辑级"新颖性/显著性"门槛**（NN 的 AE 原话：novelty marginal，未送审）。
> 因此换刊第一原则 = **目标刊流程里不能有"单方面以新颖性桌面退稿"的机制**，且评审标准要与本文实际贡献对齐。
>
> **首选 TMLR**，官方接受标准原文（2026-10-18 抓取）：
> - 第一判据是 **"claims supported by accurate and convincing evidence"**（正是 A1 最强项：匹配 gap 控制、200 方向控制、
>   三骨干复现、量化边界、可复现归档）；
> - 明确写着 **"novelty of the studied method is not a necessary criterion for acceptance in TMLR"**，并回避
>   significant/impactful/novel 三个词 —— 直接删掉 A1 的死因；
> - 流程特征：**双盲（须匿名）**、**不限长度**、TMLR 样式、附录可放证明、OpenReview 开放修订、**无 APC**、无桌面退稿环节。
>
> **次选/兜底**：Pattern Analysis and Applications（先核字数政策）→ MVA / Visual Computer → IEEE Access（有 APC）。
> **IVC 仍排除**（上限 7,500 词，本稿 ~14k–17.7k 词）。
>
> 改造清单（估 1 个工作日）：换 tmlr.sty、匿名化（含自引与仓库链接）、命题证明入附录、补充材料匿名打包、摘要压到 ~230–250 词。
> 详见 `docs/A1_VENUE_DECISION.md` §十二。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    v = io.open(VENUE, encoding="utf-8").read()
    if "十二、2026-10-18 重选" not in v:
        io.open(VENUE, "w", encoding="utf-8", newline="").write(v.rstrip("\n") + SECTION)
        print("  venue doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 换刊决策：首选 TMLR" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("71. 📮 **A1 换刊：首选 TMLR（2026-10-18 14:10）** —— NN 桌面拒后按「评估维度对齐」原则换刊：TMLR 官方标准明写 **novelty 不是接受必要条件**、第一判据是 **证据是否支持主张**；双盲/不限长度/无 APC/无桌面退稿环节。"
           "次选 PAA（先核字数）→ MVA/Visual Computer → IEEE Access（有 APC）；**IVC 仍排除**（上限 7,500 词）。"
           "改造清单（tmlr.sty + 匿名化 + 证明入附录 + 补充材料）见 `docs/A1_VENUE_DECISION.md` §十二。\n")
    if "A1 换刊：首选 TMLR" not in m:
        anchor = "70. 🧩 **A1 第 5 步"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row.replace("\\n", "\n") + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
