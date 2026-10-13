# -*- coding: utf-8 -*-
r"""补落账：本次（2026-10-13）的目录整理（2026-10-13）。

## 为什么需要补

我第一次落账用 `if "目录整理" not in ht` 做判据 —— 但 **HANDOFF 里已有一条 2026-09-29 的
"目录整理"**（当时整理 PRL 的一次性脚本）⇒ **判据被旧条目命中，写入被跳过**。

**⇒ 教训：判据串必须唯一化。** 用 `P3_PRL_revision` + `_bak_archive` 这种本次特有的串。

    python tools\_p544_record_tidy_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

MARK = "_bak_archive"          # 本次特有
ENT = """> **🗂 2026-10-13 22:00 —— 目录整理（P3 修订交付后）**
>
> ### 一、修订包位置
>
> **`SUBMISSION/P3_PRL_revision/`** —— 33 个文件，2.1 MB。
>
> | 路径 | 用途 |
> |---|---|
> | `manuscript/main.pdf` | **投稿件 = 10 页** |
> | `manuscript/supplementary.pdf` | **补充材料 = 5 页** |
> | `manuscript/main_full.pdf` | **完整版存档 = 13 页**（非投稿件） |
> | `manuscript/latex_source/` | **LaTeX 源 12 个**（编辑部要求必须上传） |
> | `response/P3_RESPONSE_LETTER.md` | **33 条正式回复**（按审稿人分组，意见原文 + 其下回复） |
> | `response/P3_REVIEW_RESPONSE.md` | 应答工作文档 |
> | `reviews/` | 审稿意见原文（邮件 + PDF + 提取文本） |
> | `evidence/` | 三组补实验报告 + 意见解析/结构化 JSON + 篇幅量化 |
> | `_superseded/` | 已过期件（`main_REVISING.pdf`，10-13 03:55 的 14 页中间版） |
>
> ### 二、整理动作（**全部是"归档 + 记账"，未删除任何文件**）
>
> | 动作 | 结果 |
> |---|---|
> | `paper3/paper_ieee/**` 的 **56 个 `.bak_*`**（1.1 MB） | → **`paper3/paper_ieee/_bak_archive/`**，含 `MANIFEST.md` 逐个标注来历脚本 |
> | **顶层 45 个文件** | → **18 个**（源 + PDF 交付件）；构建产物 **20 → `_build/`**、测试件 **6 → `_scratch/`**、过期 zip **1 → `_superseded/`** |
> | 修订包内 `main_REVISING.pdf` | → `P3_PRL_revision/_superseded/` |
> | `SUBMISSION/README.md` | 已补 `P3_PRL_revision/` 状态行 + **单列一节说明三个 P3 目录的关系** |
>
> **移动前断言**：目标绝对路径必须在 `paper3/paper_ieee/` 内（`tools/_p542` 内置 assert）。
> **整理后重新编译验证：10 页 / 0 错误 / 0 未定义** ✅
>
> ### 三、三个 P3 目录的关系（已写入 `SUBMISSION/README.md`）
>
> | 目录 | 是什么 | 能不能投 |
> |---|---|---|
> | `P3_PRL/` | **首次投稿版**（2026-09-26，11 页） | ❌ 历史存档 |
> | **`P3_PRL_revision/`** | **本次 Revise 提交包**（10 页 + 5 页补充 + 33 条回复） | ✅ **当前投稿件** |
> | `Review_PRL/` | 综述 Commentary，**另一篇、另一稿号**（`PRLETTERS-D-26-02402`） | ✅ 在审（与本稿无关） |
>
> ### 四、⚠️ 一处待核（**未处置**）
>
> `paper3/paper_ieee/Reviewer.pdf`（**1.3 MB**）**来源不明** —— 可能是本稿的审稿意见扫描件，
> 也可能是他稿材料。**已标注，未移动**，待操作者确认。
>
> ### 五、⚠️ 我自己的一个错（判据串不唯一）
>
> 第一次落账用 `if "目录整理" not in HANDOFF` 做判据 ⇒ **被 2026-09-29 的旧"目录整理"条目命中，
> 写入被静默跳过**。**⇒ 教训：落账判据必须用本次特有的串**（如 `P3_PRL_revision`、`_bak_archive`）。
> **这与"扫描器漏抓旧主张"同源 —— 判据的覆盖范围决定了它能发现什么。**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if MARK in t:
        print(f"  已含 {MARK}（本次条目已在）")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in (MARK, "2026-10-13 22:00", "33 个文件", "Reviewer.pdf", "判据串不唯一"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
