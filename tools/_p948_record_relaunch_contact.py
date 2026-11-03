# -*- coding: utf-8 -*-
r"""Record the full LLaVA relaunch and the editorial-office contact route.

Two things from this turn:

1. The full LLaVA sweep was relaunched with the **original** parameters at 17:42:09 (PID 16676), logging to
   `outputs/analysis/_p838_llava_full.out`. The frozen arm's three records were recognised and skipped, so
   it starts on `text_only_s42`. The first batch reports 1230 tokens, mean 615, sequence length 615 --
   identical to the measured configuration, which confirms `--max-len 2048` is not being filled.
2. Elsevier's official route for a message about a submission is the submission system's own **Send
   E-mail** (Author Main Menu -> the submission -> Action -> Send E-mail), not an ordinary email client:
   the message is then retained in the submission's official correspondence history. If a journal has that
   function switched off, the support chat forwards the message. An Outlook message is only appropriate if
   the journal publishes an editorial-office address.

    python tools/_p948_record_relaunch_contact.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "LLaVA 全量已按原参数重启"

ENT = """> **🚀 2026-10-15 17:50 —— LLaVA 全量**按原参数重启**；并确定联系编辑部的正规通道**
>
> ### 一、✅ 全量跑已启动（操作者选 A：原参数）
>
> | 项 | 值 |
> |---|---|
> | 启动 | **17:42:09，PID 16676** |
> | 参数 | `--samples 400 --eval-pairs 300 --epochs 3 --batch 2 --max-len 2048 --seeds 3 --rank 8 --arms frozen,text_only,vision_only,both`（**与 13:02 那次逐字相同**）|
> | 日志 | `outputs/analysis/_p838_llava_full.out`（UTF-16，PowerShell `*>>` 所致）|
> | 进度文件 | `outputs/llava_sites/train_progress.json`（每心跳覆写）|
> | 已完成 | **3 个 frozen 记录被正确识别并跳过**（`already complete, skipping`）|
> | 当前 | `text_only_s42` 训练中，GPU **100% / 7.7 GB** |
> | **首批实测** | **1230 tokens，每序列 615，序列长度 615** ⇒ **与基准配置完全一致**，再次确认 **`max-len 2048` 未被吃满** |
> | 预计 | 剩余 **9 个 run ≈ 5.4 天**（每 run ≈14.5 h）|
>
> ### 二、📮 「直接 outlook 传吗」→ **按 Elsevier 官方流程：不用 Outlook，用投稿系统内的 Send E-mail**
>
> Elsevier 官方（Journal Article Publishing Support Center，2026-08-28 更新）明确：
> **通讯作者应在投稿系统内发信给编辑/编辑部**，这样信息会**留存在该稿件的官方往来记录（Correspondence）里**；
> 若某刊未启用该功能，则用页面右下角 **"Chat with us"** 转达。
>
> **操作路径**：登录该刊 Editorial Manager → **Author Main Menu** 中找到本稿 →
> **Action 列点 `Send E-mail`**（若链接被折叠，先点 `Action Links`）→ 选最接近的模板 →
> `Customize Letter` → 保留模板自带的识别信息 → `Preview and Send` → `Send E-mail`。
> 之后可在该稿的 **Correspondence** 里看到自己发出的信。
>
> **Outlook 只在一种情况下合适**：该刊**公开了编辑部邮箱**（PRL 的作者指南为 ScienceDirect 页面，
> 本次抓取被 403 拦下，**未取得官方邮箱地址**）。若确实要发邮件，应：用**机构邮箱**
> （hw4c24@soton.ac.uk）、**主题写稿号+题名**、正文与我们准备的后续信一致，并**同时**在系统内补一条，
> 以免只留在私人邮箱里。
>
> ### 三、✅ 后续信已就绪（纯文本、80 列、无标记）
>
> `SUBMISSION/P3_PRL_revision/EMAIL_TO_EM_2026-10-15_FOLLOWUP_under_review.txt`
> —— 承认已进入 Under Review；给编辑部**两个选项**（**现在替换** / **保持现状、留到修订阶段**）；
> 只要**一行回复**表明偏好，以免留下悬空的申请。
>
> ### 四、⏳ 之后
>
> | 编辑部回 | 动作 |
> |---|---|
> | **可以现在换** | 上传 `UPLOAD_2026-10-15/`：**两个带稿号 PDF + 源码包**（三件）|
> | **保持现状** | 等 R2 决定时三件一起带上（内容与本次替换件**完全相同**）|
>
> ⚠️ **仍未做也不会做**：不撤稿、不重投、不催审——`Under Review` 下作者端不能自行替换，
> 动用"发起修订"会**打断外审**。
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
    row = ("30. 🚀 **LLaVA 全量按原参数重启 + 联系编辑部走系统内 Send E-mail（2026-10-15 17:50）** —— "
           "全量 **17:42:09 / PID 16676**，参数与 13:02 那次逐字相同，日志 `_p838_llava_full.out`，"
           "3 个 frozen 记录已跳过；首批实测 **1230 tokens / 每序列 615**（再次确认 max-len 2048 未吃满）；"
           "剩余 9 run **≈5.4 天**。**「outlook 传吗」→ 不用**：Elsevier 官方要求通讯作者用投稿系统内 "
           "**Send E-mail**（Author Main Menu → 本稿 → Action → Send E-mail → Customize Letter → Preview and Send），"
           "信件会留存在该稿 **Correspondence**；若该刊未启用，则用页面右下 **Chat with us** 转达。"
           "后续信已备 `EMAIL_TO_EM_2026-10-15_FOLLOWUP_under_review.txt`。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 17:50 条目。\n")
    anchor = "29. 📥 **P3 已进入 Under Review（2026-10-15 17:35）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
