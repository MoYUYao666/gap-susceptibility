# -*- coding: utf-8 -*-
r"""Record the SCI-only constraint and supersede the TMLR recommendation.

The operator's constraint (2026-10-18): the target must be an SCI-indexed journal. TMLR (JMLR family, no Web of Science
indexing, no impact factor) therefore drops out. This appends the corrected shortlist to the venue document and marks
the TMLR recommendation as superseded rather than deleting it.

    python tools/_p1230_record_sci_venue.py [--apply]
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

## 十三、2026-10-18 修正：**必须有 SCI 收录** ⇒ TMLR 排除，改按 SCI 重排

> 操作者约束（原文）："注意必须是SCI期刊的"。
> **§十二 的 TMLR 建议作废**：TMLR 属 JMLR 系期刊，**未被 Web of Science / SCIE 收录**（无影响因子），不满足约束。
> 原文保留在 §十二 作为决策历史。

**筛选口径**（按顺序）：① SCIE 收录；② 能容纳 A1 现稿长度（正文 ~14k 词 / 45 页）；③ scope 覆盖"视觉–语言模型的
对齐/表征分析"；④ 新颖性门槛与 A1 的实际贡献（严谨对照 + 可识别性 + 量化边界）匹配；⑤ 无已投冲突。

| 顺位 | 期刊（出版社） | SCI | scope 与 A1 匹配 | 长度政策 | 费用 | 主要风险 |
|---|---|---|---|---|---|---|
| **1** | **Pattern Analysis and Applications**（Springer）| SCIE | 高：模式分析/表征学习/深度模型分析 | 无严格字数上限（长文可）| 订阅制免费；OA 可选 | 影响力中等（Q2–Q3）；需按 Guide 复核 |
| **2** | **Machine Vision and Applications**（Springer）| SCIE | 较高：视觉方法与应用分析 | 无严格字数上限 | 订阅制免费；OA 可选 | 偏"应用"，需强化应用落点 |
| **3** | **Journal of Visual Communication and Image Representation**（Elsevier）| SCIE | 较高：视觉表征/图像–语言 | 无严格字数上限 | 订阅制免费；OA 可选 | 编辑部对"分析型"论文兴趣不稳定 |
| **4** | **Expert Systems with Applications**（Elsevier）| SCIE | 中：应用型 AI，接受实证研究 | 允许长文 | 订阅制免费；OA 可选 | 卷量大、桌面拒率高；需"应用/决策"落点 |
| **5** | **IEEE Access**（IEEE）| SCIE | 中：广谱工程与应用 | 无严格限制 | **APC ≈ 2,000 USD 量级（按当期）** | 声望较低；快 |
| ❌ | **TMLR** | **非 SCI** | —— | 不限 | 免费 | **违反约束** |
| ❌ | Neurocomputing / Neural Networks / Pattern Recognition / TNNLS / PRL / IVC | SCIE | —— | —— | —— | 已拒过（前两者桌面拒）；IVC 字数上限 4,500–7,500 不兼容 |

**结论**：首选 **Pattern Analysis and Applications**；若其 Guide 出现字数/页数硬限，则退到 **Machine Vision and
Applications**。**投稿前必须先下载目标刊 Guide 核字数政策**（IVC 的教训：不核政策就选刊等于白做）。
"""

ENT = """> **📮 2026-10-18 14:35 —— A1 选刊修正：必须有 SCI ⇒ TMLR 排除，改首选 Pattern Analysis and Applications**
>
> 操作者约束"必须是SCI期刊的" ⇒ **§十二 的 TMLR 建议作废**（TMLR 未收录于 SCIE、无影响因子；原文保留为决策历史）。
>
> 按 ①SCIE 收录 ②能容 45 页/14k 词 ③scope 匹配 ④新颖性门槛匹配 ⑤无已投冲突 重排：
> 1. **Pattern Analysis and Applications**（Springer，SCIE）—— scope 最匹配、可容长文、订阅制免费；
> 2. Machine Vision and Applications（Springer，SCIE）；
> 3. JVCI（Elsevier，SCIE）；
> 4. Expert Systems with Applications（Elsevier，SCIE，桌面拒风险高）；
> 5. IEEE Access（SCIE，快，有 APC）。
> **IVC 仍排除**（4,500–7,500 词上限）；Neurocomputing/Neural Networks/PR/TNNLS/PRL 均已有拒稿记录。
>
> **下一步**：先下载 PAA 的 Guide for Authors 核字数/页数政策，再决定是否启动格式改造。
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
    if "十三、2026-10-18 修正" not in v:
        io.open(VENUE, "w", encoding="utf-8", newline="").write(v.rstrip("\n") + SECTION)
        print("  venue doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 选刊修正：必须有 SCI" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("73. 📮 **A1 选刊修正：必须 SCI ⇒ TMLR 排除（2026-10-18 14:35）** —— 按操作者约束重排：首选 "
           "**Pattern Analysis and Applications**（Springer，SCIE）→ MVA → JVCI → ESWA → IEEE Access（有 APC）；"
           "TMLR 因**非 SCI 收录**作废（§十二 保留为历史）；IVC 仍因 4,500–7,500 词上限排除。"
           "**下一步：先核 PAA 的 Guide 字数政策再动格式。**\\n")
    if "A1 选刊修正：必须 SCI" not in m:
        anchor = "72. 🔎 **Paper Audit"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row.replace("\\n", "\n") + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
