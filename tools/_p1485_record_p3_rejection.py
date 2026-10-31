# -*- coding: utf-8 -*-
r"""Record the P3 rejection decision (Pattern Recognition Letters, 2026-10-21) in the hand-off documents."""
from __future__ import annotations

import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
OBJ = os.path.join(REPO, "docs", "P3_REVIEWER_OBJECTIONS.md")
PLAN = os.path.join(REPO, "docs", "UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md")

ENTRY = """> **❌ 2026-10-21 16:00 —— P3 被 Pattern Recognition Letters 拒稿（`PRLETTERS-D-26-02378R1`）**
>
> EM 邮件（Editor-in-Chief **Yonghuai Liu**，2026-10-21 收到）：Associate Editor 决定 **reject**；理由原文：
> *"there are some remaining issues regarding the soundness of certain technical choice and interpretation of
> experimental results which haven't been substantially addressed in the current version."*
>
> | 字段 | 值 |
> |---|---|
> | 稿件 | P3（`paper3/paper_ieee/`）|
> | 稿号 | `PRLETTERS-D-26-02378R1` |
> | 期刊 | Pattern Recognition Letters |
> | 决定 | **Rejected**（2026-10-21）|
> | 依据 | 审稿意见在 EM 审稿平台（邮件未附正文）——**待操作者导出/粘贴** |
> | 状态更新 | 旧状态 "Required Reviews Completed" 已终结 |
>
> **下一步（待操作者决定）**：① 从 EM 平台取回审稿意见；② 决定改投目标与改稿策略。本地升级稿
> （10 页正文 + 7 页补充，含 S13 provenance、S14 五 seed、S15 消融、S16 协议移动）**保留为改投基础**，
> 不再作为 PRL 修回件。候选策略：改投 TMLR / Neural Networks / Pattern Recognition 等，或重写为
> "负结果 + 方法学" 版本；详见当日备忘（待写）。
>

"""

MAP_BLOCK = """> **❌ 2026-10-21 16:00 状态更新：P3 被 PRL 拒稿**
>
> | 稿件 | 新状态 | 依据 |
> |---|---|---|
> | **P3** | **Rejected（PRL, 2026-10-21）** | EM 邮件：EIC Yonghuai Liu；AE 以"technical choice / interpretation 的 soundness 未充分解决"为由拒稿；审稿正文在 EM 平台 |
>
> 旧条目 "Required Reviews Completed（2026-10-20）" **已终结**。本地升级稿（10+7 页）转为改投基础；改投目标与改稿策略**待操作者决定**。
>

"""

ROW = ("132. ❌ **P3 被 PRL 拒稿（2026-10-21 16:00）** —— `PRLETTERS-D-26-02378R1`，EIC Yonghuai Liu；AE 理由："
       "technical choice / experimental interpretation 的 soundness 未充分解决；审稿正文在 EM 平台（待取回）；"
       "本地 10+7 页升级稿转为改投基础；改投目标待定。\n")


def main() -> int:
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "P3 被 Pattern Recognition Letters 拒稿" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "P3 被 PRL 拒稿" not in m:
        i = m.find("# 文件地图")
        j = m.find("\n", i)
        m = m[: j + 1] + "\n" + MAP_BLOCK + m[j + 1:]
        idy = m.find("131. ⬆️ **五篇升级主张")
        if idy >= 0:
            end = m.find("\n", idy)
            m = m[: end + 1] + ROW + m[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(m)
        print("  file map updated")
    if os.path.exists(OBJ):
        t = io.open(OBJ, encoding="utf-8").read()
        if "2026-10-21：PRL 拒稿" not in t:
            io.open(OBJ, "w", encoding="utf-8", newline="").write(
                t.rstrip() + "\n\n## 2026-10-21：PRL 拒稿（决定记录）\n\n"
                "- 稿号 `PRLETTERS-D-26-02378R1`；EIC Yonghuai Liu；AE 决定 reject。\n"
                "- 理由原文：*remaining issues regarding the soundness of certain technical choice and interpretation of "
                "experimental results which haven't been substantially addressed in the current version.*\n"
                "- 审稿意见正文在 EM 平台，**待操作者导出**；导出后逐条对照本文件已列 objection 更新状态。\n"
                "- 本地升级稿（10+7 页）转为**改投基础**，不再走 PRL 修回流程。\n")
            print("  P3 reviewer-objections doc updated")
    if os.path.exists(PLAN):
        t = io.open(PLAN, encoding="utf-8").read()
        if "P3 被 PRL 拒稿" not in t:
            io.open(PLAN, "w", encoding="utf-8", newline="").write(
                t.rstrip() + "\n\n> **2026-10-21 16:00 状态**：P3 **被 PRL 拒稿**（`PRLETTERS-D-26-02378R1`，EIC Yonghuai Liu）。\n"
                "> 原修回计划（response 模板/cover letter）转为改投基础；改投目标与改稿策略待定。\n")
            print("  upgrade plan updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
