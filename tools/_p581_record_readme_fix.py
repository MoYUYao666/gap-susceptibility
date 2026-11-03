# -*- coding: utf-8 -*-
r"""落账：README 修复（我的第 35 个错）（2026-10-14）。

    python tools\_p581_record_readme_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔧 2026-10-14 04:30 —— README 修复（我的第 35 个错：改发布副本被同步回滚）**
>
> ### 一、操作者发现
>
> > **"readme 没更新"**
>
> **⇒ 属实。** 我 `_p558` 改的是 **`publish_clean/README.md`**，
> 但随后 `_p571`/`_p574` 的同步**把仓库根 `README.md`（旧版 3,527 字符）复制进 `publish_clean/`**
> ⇒ **覆盖掉修改** ⇒ 推出去的是**旧 README**（仍在宣传 unique / phase transition $r_c$ /
> $32\\times$ / 181 runs / TNNLS）。
>
> **⇒ 教训：改「发布件」必须改**源头**（这里两处都要写），否则下一次同步就回滚。**
> **已修改同步脚本**：`_p574` **不再复制根 `README.md`**，发布 README 单独维护。
>
> ### 二、✅ 修复（`tools/_p579`）：两处同时写
>
> | 文件 | 改前 | 改后 |
> |---|---|---|
> | `README.md`（仓库根） | 3,527 字符 | **6,098 字符** |
> | `publish_clean/README.md` | 3,527 字符 | **6,098 字符** |
>
> **复核**：旧主张残留**全 0**（`unique admissible` / `reduces uncertainty by` /
> `phase transition at $r_c$` / `Prepared for IEEE TNNLS` / `181 runs` / `ICLR format backup`）；
> **新四节全在**（Hardware and environment / Data availability / Citation / License）+
> 新口径（`additivity axiom`、`bracketed`、`126 + 57`、`PRL (Revise)`）。
>
> ### 三、✅ 推送与远端核验
>
> | 项 | 结果 |
> |---|---|
> | 提交 | **`3b676b1`**（`dfdb38c..3b676b1`） |
> | 推送 | ✅ 成功 |
> | **远端 README**（经 `gh api` 读回） | **6,098 字符 / 135 行**；新四节 **7/7 ✅**；旧主张 **6/6 全 0 ✅** |
> | tag | 已移到 `3b676b1`（**含修正后的 README**，让 Zenodo 快照也带上） |
> | Release | ⚠️ 重建 tag 曾使其变 **Draft** ⇒ **已删除并重新发布**：`isDraft: false`、`Latest` |
>
> **Release URL**：https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v1.0-prl-revision
>
> ### 四、⚠️ Zenodo DOI 仍差一步：**仓库是私有的**
>
> `gh repo view` 确认 **`isPrivate: true`**。
> **Zenodo 对私有仓库也能发 DOI，但 DOI 落地页要求登录** ⇒ 不满足 Option C 的「读者可访问」。
> **⇒ 需操作者：GitHub → Settings → General → Danger Zone → Change visibility → Public**；
> 之后 Zenodo 的 **Upload** 页会出现 `10.5281/zenodo.XXXXXXX`。
>
> **拿到 DOI 后改三处**：① 稿件 Data statement ② cover letter 的 `[REPOSITORY DOI]`
> ③ EM 表单 Data availability ⇒ 重编译重传 `main.pdf` 与 `cover letter.pdf`。
> （README 的 Data availability 一节已写 "see the badge above"，DOI 徽章可直接贴在那里。）
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "README 被同步回滚" in t:
        print("  已记录")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("README 被同步回滚", "3b676b1", "6,098 字符", "isPrivate: true", "不再复制根"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
