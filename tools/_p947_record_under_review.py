# -*- coding: utf-8 -*-
r"""Record that P3 moved to Under Review while the replacement request was pending.

    python tools/_p947_record_under_review.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "P3 已进入 Under Review"

ENT = """> **📥 2026-10-15 17:35 —— P3 状态变为 **Under Review**（替换申请已发出，同日）**
>
> 操作者报告：**P3（`PRLETTERS-D-26-02378R1`）现在显示 Under Review**，而**当天已发出替换件申请**，
> 问「怎么办」。
>
> ### 一、✅ 不是问题：两件事**互不冲突**
>
> | 事实 | 含义 |
> |---|---|
> | EM 状态 `Under Review` | **审稿人已拿到"13 日上传的那一版"文件**，作者端**不能**自行替换 |
> | 已发出的申请 | 是给**编辑部**的询问（Send E-mail / query form），**不触发**任何重新提交或状态回退 |
> | 因此当前状态 | **一个待回复的询问 + 正在进行的外审**；**什么都没坏** |
>
> ⚠️ **关键判断**：**不要**为了换文件去动用 EM 的"发起修订/撤稿重投"功能——那会**打断外审**、
> 让审稿人重来，代价远大于那几个指针。
>
> ### 二、📄 已备好后续信（不重复论证，只问**时点**）
>
> `SUBMISSION/P3_PRL_revision/EMAIL_TO_EM_2026-10-15_FOLLOWUP_under_review.txt`
> （纯文本、80 列、无标记）要点：
>
> 1. 说明已看到进入 Under Review；
> 2. 给编辑部**两个选项**：**现在替换**（可立刻上传三件）／**保持现状**（缺陷纯属排版，
>    **不改任何结果、数字、图、结论**，可在**修订阶段**一并改）；
> 3. 只要**一行回复**表明偏好，以免留下悬空的申请。
>
> ### 三、🎯 我的建议：**发这封后续信，然后照常外审**
>
> * **发**：成本一行字，能把"申请是否还有效"问清楚，避免审稿人拿着坏引用读到一半；
> * **不做**：不撤稿、不重投、不催审；
> * **若回"保持现状"** ⇒ 一切照常，等 R2 决定时**把三个文件一起带上去**（与本次替换件**完全相同**，
>   已备好：`UPLOAD_2026-10-15/`）；
> * **若回"可以现在换"** ⇒ 直接上传 `UPLOAD_2026-10-15/` 中**带稿号的两个 PDF + 源码包**。
>
> ### 四、✅ 替换件与"两个版本"的说明（若审稿人问到）
>
> 正文与提交版的差别**只有 5 个数字**（节指针），句子一字未改：
> `S1--S6 → S1--S9`、样本量 `S3→S9`、第二数据集 `S3→S9`、秩缩放 `S4→S5`、与先前工作比较 `S5→S9`；
> 补充材料修好 **8 处交叉引用**并补上**样本量表**；源码包按新源码重建（17 条目，解压后独立编译 10 页 + 6 页）。
>
> **⇒ 对审稿结论无实质影响，这也是我在申请信里首先声明的。**
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("29. 📥 **P3 已进入 Under Review（2026-10-15 17:35）** —— 同日已发替换申请，两者**互不冲突**："
           "审稿人持有 13 日版本、作者端不能自行替换，而申请是给编辑部的询问、**不触发重投**。"
           "⚠️ **不要**为换文件动用「发起修订/撤稿重投」——会打断外审。已备后续信 "
           "`EMAIL_TO_EM_2026-10-15_FOLLOWUP_under_review.txt`（只问时点，给编辑部「现在换」/「保持现状」两个选项）。"
           "若回保持现状 ⇒ 等 R2 决定时把三件一起带上（即 `UPLOAD_2026-10-15/`，已就绪）。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 17:35 条目。\n")
    anchor = "28. 🔬 **LLaVA 每步 85 s 已定位（2026-10-15 17:25）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
