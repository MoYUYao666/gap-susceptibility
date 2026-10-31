# -*- coding: utf-8 -*-
r"""落账：从 GitHub 移除 docs/（2026-10-14）。

    python tools\_p583_record_docs_removal.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
SLUG = "MoYUYao666/gap-susceptibility"

ENT = """> **🚫 2026-10-14 05:00 —— 按操作者要求从 GitHub 移除 `docs/`（含 27 个敏感文件）**
>
> ### 一、操作者要求
>
> > **"不要放 docs"**
>
> ### 二、🔴 移除前清点：`docs/` 含 27 个**敏感文件名**
>
> `publish_clean/docs/` = **141 个文件 / 13 MB**（其中 git 已跟踪 133 个），含：
> `A1_REVIEWER_RESPONSE_PLAN.md`、`A1_ADVERSARIAL_REVIEW.md`、`A1_VENUE_DECISION.md`、
> `P23_ROUND3_REVIEW.md`、`P1_REVIEW2_*.md`、`AP3_SUBMISSION_READINESS.md`、
> **`_inbox/P3_reviews/`**（审稿意见原文）、`guides/`、`superpowers/plans/`…
>
> **⇒ 这些是审稿报告、回复计划、投稿策略与期刊决策** ——
> **多篇稿件仍在审理中，公开它们不妥。操作者的要求是对的。**
>
> ### 三、✅ 执行（`tools/_p582`）
>
> | 动作 | 结果 |
> |---|---|
> | `git rm -r --cached docs` | ✅ 移除 **133** 个跟踪文件 |
> | **本地留存** | ✅ **141 个文件复制到 `_removed_from_publish/docs/`（未删除）** |
> | `.gitignore` | ✅ 加 `docs/` + `*.bak` / `*.bak_*` / `*.orig` |
> | 提交 | **`9d9fbd5`**（"Do not publish docs/"）、**`c4a6c22`**（"Remove a stray local backup file"） |
> | 推送 | ✅ `3b676b1..9d9fbd5`、`9d9fbd5..c4a6c22` |
> | tag | 已重打到 **`c4a6c22`**（让 Zenodo 快照也不含 `docs/`） |
> | Release | 已重建：`isDraft: false`、`Latest`、`targetCommitish: main` |
>
> **另一个残留也清了**：`README.md.bak_p579`（我 `_p579` 的备份）曾被推上去 ⇒ 已移除并加进 `.gitignore`。
>
> ### 四、✅ 远端最终状态（`gh api` 核验）
>
> ```
> .gitignore  README.md  requirements.txt
> exp/  experiments/  outputs/  src/  tools/
> ```
> **8 项 —— `docs/` 已不存在**（`gh api repos/.../contents/docs` 返回 Not Found）。
>
> **Release**：https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v1.0-prl-revision
>
> ### 五、⚠️ 一处需要操作者知道的历史遗留
>
> **`docs/` 的内容仍在 git 历史里**（`1ca7744` 及之前若干提交中被跟踪）。
> **当前版本（`main` 与 tag）已不含**，但**若仓库改为公开，历史仍可被查到**。
> **⇒ 两个选项**：
> - **(a) 接受历史保留**（多数情况可接受；`docs/` 在旧提交里，不在最新快照与 Zenodo 归档中）
> - **(b) 彻底清除历史**（`git filter-repo --path docs --invert-paths` + force push）
>   —— **会重写历史**，需确认无其他人基于该仓库工作
>
> **我的建议：先 (a)** —— Zenodo 归档的是 **release 快照**（`c4a6c22`，不含 `docs/`），
> 而审稿人拿到的 DOI 指向快照；**无需为历史重写冒风险**。若日后要公开长期仓库，再做 (b)。
>
> ### 六、Zenodo DOI 仍差一步
>
> 仓库仍 **`isPrivate: true`** ⇒ 需 **Settings → General → Danger Zone → Change visibility → Public**，
> 之后 Zenodo 的 Upload 页出现 `10.5281/zenodo.XXXXXXX`。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "从 GitHub 移除 `docs/`" in t:
        print("  已记录")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("从 GitHub 移除 `docs/`", "27 个**敏感文件名", "_removed_from_publish", "c4a6c22", "历史"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")

    # 核验远端
    r = subprocess.run(["gh", "api", f"repos/{SLUG}/contents", "--jq", ".[].name"],
                       capture_output=True)
    names = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    print(f"  远端顶层：{names}")
    print(f"  {'✅' if 'docs' not in names else '🔴'} docs 不在远端")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
