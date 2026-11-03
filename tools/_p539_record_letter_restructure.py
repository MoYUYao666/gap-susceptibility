# -*- coding: utf-8 -*-
r"""落账：回复信改为「审稿人分组 + 意见原文 + 其下回复」（2026-10-13）。

    python tools\_p539_record_letter_restructure.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📝 2026-10-13 21:00 —— 回复信改为**「审稿人分组 + 每条意见原文 + 其下直接回复」**（操作者要求）**
>
> ### 一、操作者要求
>
> > **"回复是三个审稿人的评论底下分别回复"**
>
> **⇒ 结构改为**（EM 表单里审稿人逐条读"我的意见 → 作者答复"，无需来回对照）：
>
> ```
> # Response to Reviewers（变更汇总表 + 篇幅说明 + 溯源纪律）
> ---
> # Reviewer 1
> ## Comment R1.1
> > <意见完整原文>
> **Response.** <回复>
> ## Comment R1.2 …
> ---
> # Reviewer 2  …  # Reviewer 3 …
> ```
>
> **⚠️ 与旧版的关键区别**：旧版每条**只引一行意见摘要**；新版**呈现意见完整原文**（来自
> `outputs/analysis/p3_reviews_structured.json`）。
>
> ### 二、✅ 结构核验（`tools/_p536`、`_p538`）
>
> | 项 | 结果 |
> |---|---|
> | 审稿人分节头 | **3**（Reviewer 1 / 2 / 3） |
> | **Reviewer 1** | **5 条**（R1.1–R1.5）✅ |
> | **Reviewer 2** | **5 条**（R2.1–R2.5）✅ |
> | **Reviewer 3** | **23 条**（R3.1–R3.23）✅ |
> | Comment 标题 / Response 块 | **33 / 33** ✅ |
> | 意见引用块 | **33 行**（每条一行起）✅ |
> | 总规模 | **680 行 / 44,226 字符** |
>
> ### 三、✅ 字节核验（项目规矩：判编码先看字节）
>
> | 副本 | 字节 | 字符 | NUL | BOM | 编码 |
> |---|---|---|---|---|---|
> | `docs/P3_RESPONSE_LETTER.md` | 44,309 | 44,226 | 0 | False | ✅ UTF-8 合法 |
> | `SUBMISSION/…/response/P3_RESPONSE_LETTER.md` | 44,309 | 44,226 | 0 | False | ✅ |
> | `SUBMISSION/…/response/P3_RESPONSE_LETTER.txt` | 44,309 | 44,226 | 0 | False | ✅ |
>
> **⇒ 三副本 sha256 完全一致（`ca1d0997525bad7e`）。**
> **⇒ 修订包内的两个副本已同步。**
>
> ### 四、⚠️ 本次踩到的两个坑（都已修，值得记）
>
> | # | 坑 | 后果 | 修法 |
> |---|---|---|---|
> | ① | 重建脚本丢开头的 `# Reviewer 1` 定位，把旧版**残留的分节头**当成回复结尾 | **`# Reviewer 2`/`# Reviewer 3` 各出现两次** | `_p535` 加**幂等剥离**：`re.sub(r"\\n*---\\n+# Reviewer \\d+\\s*", "\\n", txt)` |
> | ② | **`git show eaa41c2:path > file`**（PowerShell 重定向） | **41,456 → 84,362 字符**（UTF-8 被当 UTF-16 处理） | 改用 **Python `subprocess` 读 stdout 字节 + 显式 `.decode("utf-8")`** |
>
> **⇒ 坑② 是本项目**第 N 次**"PowerShell 读写破坏编码"** —— 与 `Get-Content` 读 GBK 那次同源。
> **⇒ 新增纪律**：**任何"从 git 导出文本到文件"的动作，都必须用 Python 读字节，不经 shell 重定向。**
>
> ### 五、两处"疑似问题"经核实为**误报**
>
> | 标记 | 实况 |
> |---|---|
> | `runs[90]` 不在信里 | **在，2 处**（`ode_ledger.json::runs[90]`）—— 我检查用的正则太字面 |
> | `reduces uncertainty by` 出现 1 处 | **出现在审稿人自己的意见原文里**（R3.20 的评语），**不是我方主张** ✅ |
>
> ### 六、状态
>
> - **回复信**：**33/33 条**，按审稿人分组，意见原文 + 其下回复，**44,226 字符**
> - **修订包**：`SUBMISSION/P3_PRL_revision/`（30 个文件，回复信已同步）
> - **投稿件**：**10 页 / 0 错 / 0 未定义**
> - **剩余**：仅**提交动作**（EM 平台，由操作者执行），**deadline 2026-11-02**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "回复信改为" in t and "审稿人分组" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("回复信改为", "审稿人分组", "ca1d0997525bad7e", "84,362", "必须用 Python 读字节"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
