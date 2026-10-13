# -*- coding: utf-8 -*-
r"""落账：A1 被 Neurocomputing 拒稿 + 转投邀请（2026-10-10）。

    python tools\_docs_a1_reject.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📮 2026-10-10 —— A1 被 **Neurocomputing 拒稿**（`NEUCOM-D-26-20952`），收到转投邀请**
>
> ### 邮件事实（逐字，来源：操作者转发的编辑邮件）
>
> | 字段 | 内容 |
> |---|---|
> | 稿号 | **`NEUCOM-D-26-20952`** |
> | 标题 | *The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness* |
> | 期刊 | Neurocomputing |
> | 决定 | **拒稿**（"we will not be able to consider your manuscript"） |
> | 阶段 | **编辑初筛（desk reject）**——"after an **initial evaluation**"，**`Comments to Authors:` 与 `Editor's comments` 均无审稿意见** |
> | 编辑给出的理由 | ① "not appropriate for this journal's readership"；② "**falls within the aim and scope of our journal, it did not meet the significance level required**" |
> | **转投邀请** | 有。Elsevier Article Transfer Service；**须在 `Nov 08 2026 11:59PM` 前确认**接受或拒绝；接受后可自选目标刊 |
> | 未提供 | **邮件里没有列出可选的目标期刊清单**（只给了"点击选择"的链接） |
>
> ### ⚠️ 编辑意见的**内在矛盾**（须如实记录，不粉饰）
>
> 同一封邮件里：**"not appropriate for this journal's readership"** 与
> **"falls within the aim and scope of our journal"** **互相矛盾**。
> 第二句是**更具体、更可行动**的反馈 → **以"significance 不足"为主要判断**。
>
> ### A1 的完整投稿历程（第 **3** 次决定）
>
> | 序 | 期刊 | 稿号 | 结果 |
> |---|---|---|---|
> | 1 | Pattern Recognition Letters | `PRLETTERS-D-26-01941` | **拒**（2026-09-14，R1 六条 + R2 五条**实质意见**） |
> | 2 | **Neurocomputing** | **`NEUCOM-D-26-20952`** | **拒（desk，2026-10-10）** |
> | — | ~~IVC~~ | — | 曾定为目标刊，**2026-09-15 被 Neurocomputing 取代** |
>
> **→ 特征：两次被拒，且第二次是"significance 不足"的初筛**。
> **与第一次不同**：PRL 那次**有实质审稿意见**（可逐条修）；这次**没有**（只能从"significance"这一句倒推）。
>
> ### ✅ 重叠核查（**已跑**，防同刊系重复投稿风险）
>
> A1 与 `paper合` 同属 Elsevier 系，且都讲 modality gap → **必须查重叠**。
> `tools/_overlap_scan.py paper_a1 paper合 20` 实测：
>
> ```
> A = paper_a1 (9 files, 26820 words)   B = paper合 (22 files, 23234 words)
> common runs >= 20 words: 6, total shared words: 224
>   65 词  paper_a1/declaration.tex:27  ↔  paper合/main_nc.tex:100
>   26 词  paper_a1/main.tex:581        ↔  paper合/main_nc.tex:93
>   21 词  paper_a1/declaration.tex:23  ↔  paper合/main_nc.tex:88
> ```
>
> **→ 224 个共享词全部是「模板样板文字」（declaration / 声明句），无一句实质内容重合**
> → **两篇是独立工作，无重复投稿风险** ✅
>
> ### 待补（邮件里没有、且不能猜的）
>
> - [ ] **转投可选的目标期刊清单**（邮件只给链接）→ **需操作者点开链接后提供**
> - [ ] 若接受转投，是"**保留原稿**"还是"**需按新刊改造**"（Elsevier ATS 通常保留稿件，但仍需核对该刊 Guide）
> - [ ] 若拒绝转投，下一个目标刊（`docs/FAST_FREE_VENUE_OPTIONS.md` / `A1_VENUE_DECISION.md` 有历史候选，**但均需重新核 Guide**）
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "A1 被 **Neurocomputing 拒稿**" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("A1 被 **Neurocomputing 拒稿**", "NEUCOM-D-26-20952", "desk reject",
              "Nov 08 2026", "无一句实质内容重合", "转投可选的目标期刊清单"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    old = "**Neurocomputing 审稿中**（NEUCOM-D-26-20952）；原投 PRL 被拒后转投"
    if old in m:
        m = m.replace(old, "~~**Neurocomputing 审稿中**（NEUCOM-D-26-20952）~~ → "
                           "**已拒（desk reject，2026-10-10）**；**有 Elsevier 转投邀请，"
                           "须 2026-11-08 前确认**；再前一次 PRL 亦被拒", 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m)
        print(f"  ✅ 文件地图.md 已更新状态（{len(m.splitlines())} 行）")
    else:
        print("  ⚠️ 文件地图里未找到 A1 状态行（需手工核对）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
