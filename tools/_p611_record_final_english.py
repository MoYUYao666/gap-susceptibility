# -*- coding: utf-8 -*-
r"""落账：全英文化收尾 + 我的两个失误（2026-10-14）。

    python tools\_p611_record_final_english.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SLUG = "MoYUYao666/gap-susceptibility"

ENT = """> **🔤 2026-10-14 07:00 —— 全英文化**收尾**：6,908 → 约 50 字符；并记录我的两个失误**
>
> ### 一、🔴 我的第 36、37 个错（同一次操作里叠加）
>
> | # | 错 | 后果 |
> |---|---|---|
> | **36** | 用 **PowerShell `Add-Content`** 往 `publish_clean/.gitignore` 追加中文注释 —— **PS 默认按系统 ANSI（中文 Windows = GBK）写** | **`.gitignore` 成混合编码、非法 UTF-8**（`utf-8` 解码在偏移 2027 失败） |
> | **37** | `_p605` 修完 `.gitignore` 后我跑 `git add -A` 提交 —— **该命令把 873 个从未翻译的未跟踪文件一并收录**，commit message 却只写了 gitignore | **库里中文字符从 27 反弹到 6,908**（109 个文件） |
>
> **⚠️ 37 的两个子错误**：① 我扫"未跟踪文件"时**已经先 `git add -A` 过** ⇒ 扫描看到"未跟踪 0"⇒ **假阴性**；
> ② `git add -A` 前**没先看 `git status` 的 `??` 数量**（876 个）。
> **⇒ 新增纪律**：**`git add -A` 前必须先数 `??` 条目并核对它们是否该入库**；
> **向已存在文件追加内容一律用 Python 显式 `encoding="utf-8"`**（不用 PS 的 `Add-Content`/`Out-File`）。
>
> ### 二、✅ 修复（`_p605`、`_p608`、`_p609` + 第四轮 workflow 8 批）
>
> | 步 | 动作 | 结果 |
> |---|---|---|
> | ① | 重写 `.gitignore` 为**纯 ASCII 英文** + 修 2 个文件的全角标点 | 合法 UTF-8 ✅ |
> | ② | **排除 16 个内部文件**（`p3_reviews_structured.json`、`p3_review_classes.json`、`pr_*.json`、`claim_ledger.json` 等 —— **审稿往来与投稿策略**） | 本地留存在 `_removed_from_publish/internal_metadata/` |
> | ③ | **第四轮 8 批 workflow 译 92 个文件**（多为结果 JSON 的说明字段与 8 个 JSON 的键） | 6,908 → **约 50** |
>
> ### 三、✅ 最终核验（`tools/_p604`，**读包里的 blob**）
>
> **仍含中文：13 个文件 / 约 50 字符** —— **逐个核验过，全部指向真实存在的文件/目录**：
>
> | 文件 | 中文 | 核验结果 |
> |---|---|---|
> | `p3_stats_recon.json` | `A_由梯度预测_trainer基座.log`、`同秩对照_CLIP_B-32_r4_*.log` | ✅ **`outputs/_serial_logs/` 里确实有这些文件** |
> | `dinov2_hetero/clip_baseline_check.json` | `paper合/sections/empirical.tex` | ✅ **该路径在工作区存在** |
> | `audit/check_paperA.py`、`audit_citations.py`、`audit/verify_*.py`、`find_bib_placeholders.py`、`fix_paperA_round3.py` | `paper合/` | ✅ **是真实目录名** |
> | `.gitignore` | `paper合/` | ✅ **ignore 模式必须匹配真实目录名** |
> | `ap3_fulltext_lint.py` | `待补\|待填` | ✅ 占位符**检测正则**（功能数据） |
> | `audit_submission_pdfs.py` | `公开仓库` | ✅ 审计的**禁止串列表** |
> | `a1_recheck16.json` | `内部文档`（正则模式里） | ✅ **该检查的模式**（换成英文会与已有分支重复、改变搜索语义） |
> | `exp/README.md` | `结果`、`块级` | ✅ **shell 命令里的 zip 文件名** |
>
> **⇒ 判定：GitHub 库**实质全英文**；剩余中文全部是"路径/模式/文件名"这类**功能数据**，
> 翻译会打断功能，**按工程正确性应当保留**。**
>
> ### 四、✅ 提交与发布
>
> | 项 | 结果 |
> |---|---|
> | 提交 | **`8352d8d`**（`7ee0059..8352d8d`）：**87 修改 + 16 排除** |
> | 推送 | ✅ 成功；远端 `main = 8352d8d` |
> | tag | 已重打到 **`8352d8d`** |
> | Release | 已重建：`isDraft: false`、`Latest`；**notes 固化为包内 `SUBMISSION/P3_PRL_revision/RELEASE_NOTES.md`**（不再用临时文件） |
>
> **Release**：https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v1.0-prl-revision
> **已跟踪**：**1,946 个文件**（其中二进制 25 个）
>
> ### 五、⚠️ 一处上游提醒（agent 报告，我确认它无害但值得记）
>
> `p3d_summary.json` 的 `source_fingerprint.sha256` 是 `p3d_clip_ranksweep.json` 的**旧指纹**
> —— 后者在翻译中被改过 ⇒ **指纹现已过期**。
> **grep 全库：`source_fingerprint` 被 0 个脚本读取** ⇒ 无功能影响；
> **但既然该文件的用途就是"锁定时口径"，过期指纹应当更新**（或标注）。
> **⇒ 列为待办**（非阻塞）。
>
> ### 六、状态
>
> - **投稿件**：**10 页 / 0 错 / 0 未定义 / 0 中文**
> - **GitHub**：`main = 8352d8d`，Release `v1.0-prl-revision` 已发布，**仓库仍私有**
> - **剩余**：① 仓库改公开 ⇒ 拿 Zenodo DOI ⇒ 填三处 ⇒ 重编译重传
>   ② 修订包三份文档（`README`/`UPLOAD_CHECKLIST`/`ARCHIVE_WITH_ZENODO`）是否英文化
>   ③ `p3d_summary.json` 指纹更新 ④ EM 三个回复框 ⑤ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "第 37 个错" in t:
        print("  已记录")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("第 36、37 个错", "8,352d8d".replace("8,", ""), "Git add -A", "功能数据", "RELEASE_NOTES.md"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
