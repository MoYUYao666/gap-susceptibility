# -*- coding: utf-8 -*-
r"""落账：A-1 换刊评估的**依据与更正**（2026-10-06）。

## 本文件记录三件事

### ① **更正**：我把"A1 同刊冲突"说得过重了

先前我说：`paper合/`（Paper A）与 A1 都投 Neurocomputing 是"**同刊冲突**"。
**核对官方指南后应更正**：

- 指南里的 **"Co-submission of related data, methods or protocols"** 原文是
  *"You are encouraged to publish a **description of your research data, m[ethods or protocols]**…"*——
  指**把数据/方法说明作为配套短文一并投**（Elsevier 的 Data/MethodsX 配套机制），
  **与"同一期刊投两篇研究论文"无关**；
- 指南对"**并行投稿**"的限制是"**The article is not under consideration for publication elsewhere**"——
  指`paper合`自身不得重复投出，**不禁止同刊有多篇相关稿件**。

→ **同刊发表本身不违规**，只是需要**如实披露**（皆走投稿系统的声明，非正文）。
**真正的风险是编辑的主观判断**，不是明文禁令。

### ② **更正**：稿件声明**并无缺失**（我先前判断错误）

我曾据 `sections/*.tex` 的 grep 结果说"缺少 CRediT / Competing interests / Funding / AI 声明"。
**实际这五节都在 `paper合/main_nc.tex:80–104`**，且内容完整——
**我漏查了主文件**。**这是我的检索方法错误，不是稿件的缺陷。**

### ③ **换刊评估的硬约束（有据）**

免 APC 覆盖刊清单取自 `docs/OA_FUNDING_ROUTES.md`（三重证据：Southampton 官方页
+ **SciFree API 逐刊实测** `payment = Included in Publisher Agreement` + 操作者截图）。

**同时必须叠加"已拒稿史"**（`文件地图.md`）：

| 刊 | 与本题的关系 |
|---|---|
| **Neural Networks** | ⚠️ **P1 曾被桌面拒** |
| **Neurocomputing** | ⚠️ **P1 曾被桌面拒**；且 **A1 正在此刊在审** |
| **Pattern Recognition** | P1 **正在此刊在审**（`PR-D-26-10149`）；曾三次格式 R&R |
| Pattern Recognition Letters | P3 与 Commentary 在审；且 PRL 是 letters 刊，**篇幅不匹配 49 页** |
| **Knowledge-Based Systems** | 无拒稿史；但第三方记录审稿约 **7.8 个月**（来源：LetPub 页面，**非官方**，需复核） |
| **Expert Systems with Applications** | 无拒稿史（更正：`REVIEW_VENUE_DECISION.md` 已澄清"操作者从未投过 ESWA"） |
| Image and Vision Computing ／ Computer Vision and Image Understanding | 无拒稿史 |
| Information Fusion | 无拒稿史；但其 Survey 类别主用于综述 |

**→ 未拒过稿且免 APC 的候选**：KBS、ESWA、IVC、CVIU、Information Fusion（5 个）。

---

## ⚠️ 本阶段**未完成**的部分（诚实标注）

**我未能产出符合本项目标准的换刊对比表。** 原因：

- 本项目规则（`docs/REVIEW_VENUE_DECISION.md`）要求**官方 Guide 存本地 + 逐条对照 + 写出出处行号**；
- 本次尝试联网取 ScienceDirect 官方 Insights 页 → **HTTP 403**；
  LetPub 页面 → 内容零散、口径不一；journalmetrics.org → **HTTP 429**；
- **因此我拿不到可引用的官方数据**（审稿周期、篇幅上限、评审方式、文章类别）。
  **按规则不得用第三方数字填空。**

**要完成 A-1，需要**：候选刊的 **Guide for authors PDF**（操作者提供或允许抓取）。
已有 4 份存档：Neurocomputing、PRL、IVC、OE（`期刊指南/`）。

---

    python tools\_docs_a1_venue_note.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    apply = "--apply" in sys.argv
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    # ① 新建决策记录（本阶段交付件）
    out = REPO / "docs" / "PAPERA_VENUE_OPTIONS.md"
    body = __doc__.split('"""')[1].strip()
    header = ("# Paper A 换刊评估（A-1）—— 依据、更正与未完成项\n"
              "> 生成：2026-10-06 ｜ 脚本：`tools/_docs_a1_venue_note.py`（幂等）\n"
              "> 规则来源：`docs/REVIEW_VENUE_DECISION.md`、`docs/OA_FUNDING_ROUTES.md`\n\n---\n\n")
    io.open(out, "w", encoding="utf-8", newline="").write(header + body + "\n")
    t = io.open(out, encoding="utf-8").read()
    for k in ("SciFree API 逐刊实测", "Co-submission of related data",
              "included in Publisher Agreement", "HTTP 403", "未完成"):
        assert k in t, f"断言失败：缺 {k}"
    print(f"  ✅ 已写 {out.relative_to(REPO)}（{len(t.splitlines())} 行）")

    # ② HANDOFF 追加
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = r"""> **📋 2026-10-06 —— A-1 换刊评估：依据、**两处自我更正**、以及未完成项**
>
> ### ① **更正**：我把"A1 同刊冲突"说重了
>
> 指南里 **"Co-submission of related data, methods or protocols"** 的原文是
> *"You are encouraged to publish a **description of your research data, m[ethods or protocols]**…"*
> ——指**数据/方法说明作为配套短文一并投**（Data/MethodsX 机制），
> **与"同刊投两篇研究论文"无关**。指南的限制是"**not under consideration for publication elsewhere**"，
> 即 `paper合` 自身不得重复投出，**不禁止同刊有多篇相关稿件**。
> → **同刊发表不违规，只需如实披露**；真正的变量是编辑的主观判断，**不是明文禁令**。
>
> ### ② **更正**：稿件声明**没有缺失**（我先前判断错误）
>
> 我曾据 `sections/*.tex` 的 grep 说"缺 CRediT / Competing interests / Funding / AI 声明"。
> **实际五节都在 `paper合/main_nc.tex:80–104` 且内容完整**——我漏查了主文件。
> **是我的检索方法错误，不是稿件缺陷。**
>
> ### ③ 换刊硬约束（有据）
>
> **免 APC 覆盖**（`docs/OA_FUNDING_ROUTES.md`，三重证据：Southampton 官方页 + **SciFree API 逐刊实测**
> `payment = Included in Publisher Agreement` + 操作者截图）：Neurocomputing、Pattern Recognition、
> PRL、**Image and Vision Computing**、**Computer Vision and Image Understanding**、Neural Networks、
> **Expert Systems with Applications**、Information Fusion、**Knowledge-Based Systems**。
>
> **叠加已拒稿史**（`文件地图.md`）后，**未拒过稿且免 APC 的候选 = 5 个**：
> **KBS、ESWA、IVC、CVIU、Information Fusion**。
> （`Neural Networks` / `Neurocomputing` = P1 曾桌面拒；`Pattern Recognition` = P1 在审；
> `PRL` = P3 与 Commentary 在审，且 letters 刊篇幅不匹配 49 页。）
>
> ### ⚠️ **本阶段未完成（诚实标注）**
>
> **未能产出符合本项目标准的换刊对比表**：官方 Insights 页 **HTTP 403**、
> journalmetrics.org **HTTP 429**、LetPub 口径不一 → **无可引用的官方数据**，
> 按规则**不得用第三方数字填空**。
> **所需**：候选刊的 **Guide for authors PDF**（操作者提供或允许抓取）。
> 详见 **`docs/PAPERA_VENUE_OPTIONS.md`**。
"""
    if "A-1 换刊评估" not in h:
        anchor = "> **📐 2026-10-06 —— 图切矢量 PDF"
        i = h.find(anchor)
        if i > 0:
            io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + h[i:])
            h2 = io.open(hp, encoding="utf-8").read()
            for k in ("Co-submission of related data", "漏查了主文件", "未拒过稿且免 APC"):
                assert k in h2, f"HANDOFF 断言失败：缺 {k}"
            print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
