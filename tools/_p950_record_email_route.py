# -*- coding: utf-8 -*-
r"""Record that the submission system's Send E-mail takes no attachments, and the email version.

Operator finding 2026-10-15: Editorial Manager's "Send E-mail" has no attachment path, so the replacement
files have to travel by email. The request is therefore reissued as a plain email carrying the three
files, and it keeps the same offer: replace now, or leave the files alone and apply the same corrections
at the revision stage.

Also recorded: the full LLaVA sweep is running at **56 s per step** (faster than the 85-94 s measured
while the benchmark competed for the device), 80 of 600 steps done at 19:00, projecting about 9.3 h for
the current run and about 3.7 days for the nine that remain.

    python tools/_p950_record_email_route.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "EM 的 Send E-mail 不能带附件"

ENT = """> **📧 2026-10-15 19:10 —— EM 的 Send E-mail **不能带附件**（操作者实测）⇒ 改用**邮件直发三件**；全量跑 56 s/步**
>
> ### 一、🔍 操作者实测发现（推翻我 17:50 的建议）
>
> 我按 Elsevier 官方文档建议「用系统内 **Send E-mail**」，理由是信件会**留存在该稿 Correspondence**。
> **但操作者实测：该界面没有附件上传路径。** ⇒ 那封信**只能"请求许可"，不能"递送文件"**，
> **光靠它无法完成替换**。**我的建议因此需要修正**（官方文档只讲"写信"，没讲"递件"）。
>
> ### 二、✅ 修正后的路线：**邮件直发 + 系统内留痕**
>
> | 步骤 | 动作 |
> |---|---|
> | 1 | **Outlook 直发**：主题 `PRLETTERS-D-26-02378R1 - replacement files (manuscript, Supplementary Material, LaTeX source)`，**附三件**（共 **≈0.9 MB**）|
> | 2 | **收件人**：**用编辑部/EM 已经给你发过通知的那个地址**（通知邮件里就有），或处理编辑；⚠️ **不要猜地址**——PRL 作者指南页面本次抓取 **403**，**未取得官方邮箱**，故**不提供猜测地址** |
> | 3 | **发件人**：用**机构邮箱** hw4c24@soton.ac.uk（对应作者身份）|
> | 4 | 系统内已发的 query 继续用作**留痕**；若回信要我们从系统走，再按其指示操作 |
>
> ### 三、✅ 邮件正文已写好（纯文本、80 列、无标记、无中文）
>
> `SUBMISSION/P3_PRL_revision/EMAIL_direct_with_attachments.txt`
> 要点：① 说明**为何改用邮件**（系统消息不收附件）；② 两个缺陷**如实列明**；
> ③ **逐件说明**三件各是什么、改了什么、源码包可独立编译；④ 给编辑部**两个选项**
> （**现在替换** / **保持现状、留到修订阶段**）；⑤ 只要**一行回复**。
>
> **附件与大小**：`..._Manuscript.pdf` **406 KB**、`..._Supplementary.pdf` **265 KB**、
> `..._LaTeX_Source.zip` **224 KB**。
>
> ### 四、✅ 全量跑状态（19:00 实测）
>
> | 项 | 值 |
> |---|---|
> | 进度 | **step 80/600**（`text_only_s42`），loss **0.9844** |
> | **每步** | **56.0–56.2 秒**（**比基准的 85–94 s 更快**——基准当时与其它进程抢 GPU）|
> | 当前 run ETA | **2026-10-16 03:05**（≈9.3 h）|
> | 剩余 9 个 run | **≈3.7 天** |
> | GPU | 99–100% / 7.7 GB |
>
> **⇒ 比我 17:25 估计的 5.4 天更好**：实测 56 s/步，非 85–94 s。
>
> **工具**：`_p949`（带附件的邮件文本）｜`_p950`（本条落账）。
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
    row = ("31. 📧 **EM 的 Send E-mail 不能带附件 ⇒ 改邮件直发三件（2026-10-15 19:10）** —— 操作者实测该系统消息**无附件路径**，"
           "故我 17:50 的建议**需修正**（官方文档只讲写信、不讲递件）。修正路线：**Outlook 直发**（主题含稿号，附 "
           "`Manuscript.pdf` 406 KB + `Supplementary.pdf` 265 KB + `LaTeX_Source.zip` 224 KB，共 ≈0.9 MB），"
           "**收件人用编辑部已发通知的地址**（PRL 作者指南 403 未取得官方邮箱，**不猜地址**），系统内 query 留痕。"
           "邮件正文 `EMAIL_direct_with_attachments.txt`（纯文本、80 列）。**全量跑 56 s/步**（比基准 85–94 s 更快），"
           "step 80/600，ETA 10-16 03:05，剩余 9 run **≈3.7 天**。详见 `HANDOFF.md` 顶部 2026-10-15 19:10 条目。\n")
    anchor = "30. 🚀 **LLaVA 全量按原参数重启 + 联系编辑部走系统内 Send E-mail（2026-10-15 17:50）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
