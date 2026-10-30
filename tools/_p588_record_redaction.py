# -*- coding: utf-8 -*-
r"""落账：发布库脱敏（2026-10-14）。

    python tools\_p588_record_redaction.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SLUG = "MoYUYao666/gap-susceptibility"

ENT = """> **🔒 2026-10-14 05:30 —— 发布库脱敏（按操作者要求去掉个人信息）**
>
> ### 一、操作者要求
>
> > **"尽量不要包含我的个人信息，readme 改一下"**
>
> ### 二、处置原则（区分「身份信息」与「学术署名」）
>
> | 类 | 具体 | 处置 | 理由 |
> |---|---|---|---|
> | **联系方式** | `hw4c24@soton.ac.uk`、`2024282101@hrbeu.edu.cn` | ✅ **清掉** | 邮箱是主要被爬取目标 |
> | **账号名** | `MoYUYao666`、`hw4c24` | ✅ **清掉** | 可关联到其它平台身份 |
> | **单位** | `University of Southampton` | ✅ **从 README 头部去掉** | 减少可定位性 |
> | **姓名** | `Hongrui Wan` | ⚠️ **保留** | **学术署名** —— 去掉会使代码无法被正确引用（许可也要求保留署名） |
>
> ### 三、✅ 执行（`tools/_p586`、`_p587`）
>
> | 项 | 结果 |
> |---|---|
> | README 作者行 | `**Hongrui Wan** · University of Southampton · \`hw4c24@soton.ac.uk\`` → **`**Hongrui Wan**`** |
> | 联系方式替换 | **62 处 / 42 个文件** → 占位 `contact@example.com`（脚本里的） |
> | 账号名替换 | `MoYUYao666` → `OWNER`（构建脚本里的） |
> | **复核（本地）** | `hw4c24` / `2024282101` / `MoYUYao666` / `soton.ac.uk` / `hrbeu` **全 0** |
> | **复核（远端，经 `gh api` 读回）** | 同上**全 0**；姓名保留 **1 处** |
>
> **⚠️ 我中间犯了一个顺序错**：`_p586` 先替换邮箱、后替换作者行 ⇒ 作者行变成
> `**Hongrui Wan** · University of Southampton · \`contact@example.com\``（占位邮箱仍像联系方式、单位还在）。
> **⇒ `_p587` 已改为只留 `**Hongrui Wan**`。**
>
> ### 四、✅ 推送与发布
>
> | 项 | 结果 |
> |---|---|
> | 提交 | **`7755f70`**（`c4a6c22..7755f70`） |
> | tag | 已重打到 **`7755f70`** |
> | Release | 已重建：`isDraft: false`、`Latest` |
>
> **Release**：https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v1.0-prl-revision
> **远端 README**：6,047 字符，头部为 `# Cross-Modal Alignment under PEFT` + **`**Hongrui Wan**`**
>
> ### 五、⚠️ 两处**历史遗留的个人信息**（当前版本已不含，历史里仍在）
>
> | # | 位置 | 说明 | 处置选项 |
> |---|---|---|---|
> | ① | **commit 作者身份** | 全部 7 次提交为 `Hongrui Wan <2024282101@hrbeu.edu.cn>`；**GitHub 会把它显示在每个提交上** | (a) 用新邮箱改写历史（`git filter-repo --email-callback`）+ force push；(b) 接受 |
> | ② | **历史中的 `docs/` 与旧 README** | 旧提交里含审稿材料与旧联系方式 | 同上一节，`--path docs --invert-paths` |
>
> **⇒ 若仓库将公开，建议一并做 (a)+(b)**：一次 `git filter-repo` 同时清 `docs/` 与改写作者邮箱，
> 然后 `git push --force`（**会重写历史**；本仓库为单人项目，风险低）。
> **⇒ 若暂不公开**（当前 `isPrivate: true`），可先不动 —— **Zenodo 归档的是 release 快照，已不含这些内容**。
>
> ### 六、状态
>
> - **GitHub**：`main = 7755f70`，Release `v1.0-prl-revision` 已发布，**仓库仍私有**
> - **远端内容**：`.gitignore` / `README.md` / `requirements.txt` / `exp` / `experiments` / `outputs` / `src` / `tools`
> - **剩余**：① **仓库改公开 ⇒ 拿 Zenodo DOI**（如需彻底清历史，先做 `filter-repo`）
>   ② 把 DOI 填进稿件 Data statement / cover letter / EM 表单 ⇒ 重编译重传 ③ EM 三个回复框 ④ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "发布库脱敏" in t:
        print("  已记录")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("发布库脱敏", "7755f70", "62 处", "作者身份", "filter-repo"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    r = subprocess.run(["gh", "repo", "view", SLUG, "--json", "isPrivate,visibility"],
                       capture_output=True)
    print(f"  远端可见性：{r.stdout.decode('utf-8', errors='replace').strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
