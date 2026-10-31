# -*- coding: utf-8 -*-
r"""更新 `SUBMISSION/README.md`：加入 `P3_PRL_revision/` 并说明三者关系（2026-10-13）。

## 背景

`SUBMISSION/README.md`（2026-10-12 建立）的状态表**没有 `P3_PRL_revision/`** —— 它是本次修订新建的。
三个 P3 目录的关系必须写明，否则日后分不清哪个是投稿件：

| 目录 | 内容 | 能否投稿 |
|---|---|---|
| `P3_PRL/` | **首次投稿版**（2026-09-26，11 页） | ❌ 历史存档 |
| **`P3_PRL_revision/`** | **本次修订提交包**（2026-10-13，10 页 + 补充材料 + 33 条回复） | ✅ **投稿件** |
| `Review_PRL/` | 综述 Commentary（`-02402`，另一篇） | ✅ 在审（另一稿号） |

    python tools\_p543_update_submission_readme.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
README = REPO / "SUBMISSION" / "README.md"

OLD_ROW = "| `P3_PRL/` | P3 | Pattern Recognition Letters | `PRLETTERS-D-26-02378` | 🔄 **在审** | 11 |"
NEW_ROW = "\n".join([
    "| `P3_PRL/` | P3 | Pattern Recognition Letters | `PRLETTERS-D-26-02378` | 📦 **首次投稿版**（存档） | 11 |",
    "| **`P3_PRL_revision/`** | P3 | Pattern Recognition Letters | `PRLETTERS-D-26-02378` | 🔄 **Revise 修订包（当前投稿件）**：10 页 + 5 页补充 + 33 条回复；截止 **2026-11-02** | **10** |",
])

SECTION = """

## P3 的三个目录（**别混**）

| 目录 | 是什么 | 能不能投 |
|---|---|---|
| `P3_PRL/` | **首次投稿版**（2026-09-26 投出，11 页） | ❌ **历史存档**，不要再投 |
| **`P3_PRL_revision/`** | **本次 Revise 的提交包**（2026-10-13 生成） | ✅ **当前投稿件** |
| `Review_PRL/` | 综述 Commentary，**另一篇、另一稿号**（`PRLETTERS-D-26-02402`） | ✅ 在审（与本稿无关） |

### `P3_PRL_revision/` 内部（33 个文件）

| 路径 | 用途 |
|---|---|
| `manuscript/main.pdf` | **投稿件 = 10 页** |
| `manuscript/supplementary.pdf` | **补充材料 = 5 页**（公理推导/证明/协议细节/逐 run 表/表图） |
| `manuscript/main_full.pdf` | **完整版存档 = 13 页**（**非投稿件**，供回复信引用与审稿人索取） |
| `manuscript/latex_source/` | **LaTeX 源（12 个）** —— 编辑部要求必须上传，只交 PDF 会延误 |
| `response/P3_RESPONSE_LETTER.md` | **33 条正式回复**（按审稿人分组，意见原文 + 其下回复） |
| `response/P3_REVIEW_RESPONSE.md` | 应答工作文档（含建议动作与根问题归纳） |
| `reviews/` | 审稿意见原文（编辑邮件 + PDF + 提取文本） |
| `evidence/` | 三组补实验报告 + 意见解析/结构化 JSON + 篇幅量化 |
| `_superseded/` | **已过期件**（`main_REVISING.pdf`，10-13 03:55 的 14 页中间版） |
| `README.md` | 包内索引 + **提交前必办 4 项** |

**⚠️ 提交前必办**（详见包内 `README.md`）：
1. **cover letter 主动说明篇幅与 Guide 的 7 页关系**并请编辑裁定（回复信开头已写）
2. **上传 LaTeX 源**
3. **Authorship Confirmation 以 item type `Cover Letter` 上传**（Guide 第 4 条：未照办 = AUTOMATIC REJECTION）
4. **33 条回复要在 EM 表单逐条填写**（不能只交 PDF）
"""

ENT = """

> **📁 2026-10-13 22:00 —— 目录整理**
>
> | 动作 | 结果 |
> |---|---|
> | **`paper3/paper_ieee/**` 的 56 个 `.bak_*`**（1.1 MB） | → **`_bak_archive/`**（含 `MANIFEST.md` 逐个标注来历脚本） |
> | **顶层 45 个文件** | → **18 个**；构建产物 20 → `_build/`，测试件 6 → `_scratch/`，过期 zip 1 → `_superseded/` |
> | **修订包里 `main_REVISING.pdf`**（过期 14 页版） | → `P3_PRL_revision/_superseded/` |
> | **`SUBMISSION/README.md`** | 已补 `P3_PRL_revision/` 行 + **单列一节说明三个 P3 目录的关系** |
>
> **⚠️ 全部是"归档 + 记账"，未删除任何文件**；移动前断言目标路径在 `paper3/paper_ieee/` 内。
> **整理后重新编译验证：10 页 / 0 错 / 0 未定义** ✅
>
> **一处待核（未处置）**：`paper3/paper_ieee/Reviewer.pdf`（**1.3 MB**）来源不明 ——
> 可能是本稿审稿意见扫描件，也可能是他稿材料。**已标注，未移动**，待操作者确认。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(README, encoding="utf-8", errors="replace").read()
    print(f"  README {len(t):,} 字符")
    n_p3rev = t.count("P3_PRL_revision")
    print(f"  已含 'P3_PRL_revision'：{n_p3rev} 处")
    has_row = OLD_ROW in t
    print(f"  旧状态表行命中：{has_row}")
    if not a.apply:
        print("  （预演）")
        return 0
    if has_row:
        t = t.replace(OLD_ROW, NEW_ROW)
        print("  ✅ 状态表已插入 P3_PRL_revision 行")
    if "P3 的三个目录" not in t:
        # 插到 "_old/" 一节之前
        k = t.find("## 已失效的旧投稿")
        if k > 0:
            t = t[:k] + SECTION.strip() + "\n\n" + t[k:]
        else:
            t = t.rstrip() + "\n" + SECTION
        print("  ✅ 已加「P3 的三个目录」一节")
    io.open(README, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n")
    t2 = io.open(README, encoding="utf-8", errors="replace").read()
    for k in ("P3_PRL_revision", "P3 的三个目录", "AUTOMATIC REJECTION", "main_full.pdf"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  → {len(t2):,} 字符")

    # HANDOFF 落账
    hp = REPO / "HANDOFF.md"
    ht = io.open(hp, encoding="utf-8").read()
    if "目录整理" not in ht:
        i = ht.find("# 项目交接文档")
        j = ht.find("\n", i)
        io.open(hp, "w", encoding="utf-8", newline="").write(ht[:j + 1] + ENT + ht[j + 1:])
        print(f"  ✅ HANDOFF 已落账（{len(io.open(hp, encoding='utf-8').read().splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
