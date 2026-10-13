# -*- coding: utf-8 -*-
r"""把 A-1 换刊评估落账到 HANDOFF（2026-10-06）。

`docs/PAPERA_VENUE_OPTIONS.md` 已由 write 工具直接写出；本脚本只负责 HANDOFF 条目与断言。

    python tools\_docs_a1_handoff.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **📋 2026-10-06 —— A-1 换刊评估：依据、**两处自我更正**、与未完成项**
>
> 交付件：**`docs/PAPERA_VENUE_OPTIONS.md`**
>
> ### ① **更正**：我把"A1 同刊冲突"说重了
>
> 指南里 **"Co-submission of related data, methods or protocols"** 原文是
> *"You are encouraged to publish a **description of your research data, m[ethods or protocols]**…"*
> ——指**数据/方法说明作为配套短文一并投**（Data/MethodsX 机制），**与"同刊投两篇研究论文"无关**。
> 指南的限制是 *"not under consideration for publication elsewhere"*，即 `paper合` 自身不得重复投出，
> **不禁止同刊有多篇相关稿件**。
> → **同刊发表不违规，只需如实披露**；真正的变量是**编辑的主观判断**，不是明文禁令。
>
> ### ② **更正**：稿件声明**没有缺失**（我先前的判断错误）
>
> 我曾据 `sections/*.tex` 的 grep 说"缺 CRediT / Competing interests / Funding / AI 声明"。
> **实际五节都在 `paper合/main_nc.tex:80–104` 且内容完整**——**我漏查了主文件**。
> **是我的检索方法错误，不是稿件缺陷。**
>
> ### ③ 换刊硬约束（有据）
>
> **免 APC 覆盖**（`docs/OA_FUNDING_ROUTES.md`，三重证据：Southampton 官方页
> + **SciFree API 逐刊实测** `payment = Included in Publisher Agreement` + 操作者截图）：
> Neurocomputing、Pattern Recognition、PRL、Image and Vision Computing、
> Computer Vision and Image Understanding、Neural Networks、Expert Systems with Applications、
> Information Fusion、Knowledge-Based Systems。
>
> **叠加已拒稿史**（`文件地图.md`）后，**未拒过稿且免 APC 的候选 = 5 个**：
> **KBS、ESWA、IVC、CVIU、Information Fusion**。
> （`Neural Networks` / `Neurocomputing` = P1 曾桌面拒；`Pattern Recognition` = P1 在审；
> `PRL` = P3 与 Commentary 在审，且 letters 刊篇幅不匹配 49 页。）
>
> ### ⚠️ **本阶段未完成（诚实标注，不填空）**
>
> **未能产出符合本项目标准的换刊对比表**。规则（`docs/REVIEW_VENUE_DECISION.md`）要求
> **官方 Guide 存本地 + 逐条对照 + 写出出处行号**，但本次取证：
> ScienceDirect 官方 Insights 页 **HTTP 403** ｜ journalmetrics.org **HTTP 429** ｜
> LetPub 口径不一 → **无可引用的官方数据**，故对比表的
> **「审稿周期 / 篇幅上限 / 评审方式 / 文章类别」四列留空**。
>
> **所需**：候选刊 **Guide for authors PDF**（优先 **KBS、ESWA、CVIU**；IVC 已有存档）。
>
> ### ④ 文档矛盾已修
>
> `AGENTS.md:18` 原写 `paper合/` **"已弃用"**，与 `文件地图.md:85`
> （**2026-10-01 起已恢复为主稿**）**直接冲突**。已按"追加不重写 + 标注过期"更正如上，
> 并把目录行补齐真实刊号（`PR-D-26-10149` / `NEUCOM-D-26-20952` / `26-0663`）
> 与 **`paper合/` = 当前主稿**、**`paper_ap3/` = 因含 P3 不可投**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    # 先核验交付件存在
    vp = REPO / "docs" / "PAPERA_VENUE_OPTIONS.md"
    assert vp.exists(), "交付件 docs/PAPERA_VENUE_OPTIONS.md 不存在"
    vt = io.open(vp, encoding="utf-8").read()

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "A-1 换刊评估" in h:
        print("  HANDOFF 已记录，跳过")
    else:
        anchor = "> **📐 2026-10-06 —— 图切矢量 PDF"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 插入锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENT + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("Co-submission of related data", "漏查了主文件",
                  "未拒过稿且免 APC", "PAPERA_VENUE_OPTIONS.md", "AGENTS.md:18"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")

    # 交叉核验：HANDOFF 与交付件口径一致
    for k in ("Co-submission", "SciFree", "403", "KBS、ESWA、IVC、CVIU"):
        assert k in vt, f"交付件缺 {k}"
    print("  ✅ 交付件与 HANDOFF 口径一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
