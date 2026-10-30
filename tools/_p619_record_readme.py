# -*- coding: utf-8 -*-
r"""Record the README rewrite and the identity findings in the handoff document.

Operator (2026-10-14): "readme先只包含paper3，不要我的信息"

    python tools/_p619_record_readme.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SLUG = "MoYUYao666/gap-susceptibility"

ENT = """> **📄 2026-10-14 09:00 —— README 重写为「只有 Paper 3 + 无个人信息」；并发现两处身份泄露**
>
> ### 一、操作者要求
>
> > **"readme先只包含paper3，不要我的信息"**
>
> ### 二、🔴 先发现：**操作者已在 GitHub 网页上改过 README**
>
> 推送时被拒（`non-fast-forward`）⇒ 实测远端有**两个我没做的提交**：
>
> | 提交 | 作者 | 时间 | 内容 |
> |---|---|---|---|
> | `363fcbd` | `MoYUYao666 <hongrui998@outlook.com>` | 2026-10-13 19:55:14 | 删掉 `**Hongrui Wan**` 与 Paper 1/2 小节 |
> | `0dfdd67` | 同上 | 2026-10-13 19:55:52 | 同上续 |
>
> **⇒ 与我的意图完全一致，我的版本更完整。**
> **处置：`git merge`（不是 force push）⇒ 操作者的两个提交保留在历史里**，
> 冲突以我的完整重写解决，合并提交 **`c42c6e8`** 说明了两者关系。
>
> ### 三、✅ 新 README（`publish_clean/README.md`，5,619 字符 / 126 行）
>
> | 小节 | 内容 |
> |---|---|
> | 标题 | **Gradient Structure Laws as Predictors of PEFT Design**（不再用"Cross-Modal Alignment under PEFT"这个覆盖三篇的题） |
> | What this repository is | 只有代码与结果；**明示不含稿件/PDF/cover letter/补充材料** |
> | **The claim, and what we had to give up** | **四项撤回逐条写明**：R1–R5 需加 R3′ 公理（含 `‖∇E‖²` 反例）、分配优势在另一学习率反转且匹配损失后消失、crossing 是 bracketed 而非 sharp、30× 方差比撤回；并写明 **AdaLoRA 优于我们所有臂**（`−1468`/`−757`） |
> | Repository structure | **只列库里真实存在的路径**（`outputs/` `tools/` `src/` `exp/` `experiments/`） |
> | Hardware and environment | 三档配置（本地 8 GB / 云端 A800 / 纯 CPU） |
> | Setup | 环境搭建 |
> | Data availability | 公开数据 + 本库的**派生数据**；**每个数字可指名脚本与字段**；append-only 记录 |
> | Reproducing a reported number | 给出 `grep` + 重跑的具体做法 |
> | License | **无许可文件 ⇒ 明示"未授予许可"**（不再悬空引用不存在的 `LICENSE`） |
>
> **✅ 复核（远端，经 `gh api` 读回）**：**个人信息 0 处**（`Hongrui`/`hw4c24`/`soton`/`hrbeu`/`MoYUYao666`/`Southampton`/`outlook.com`）；
> **其它论文 0 处**（`Paper 1`/`Paper 2`/`paper2/`/`116 experiments`/`224 experiments`）。
>
> ### 四、✅ README 里每个数字都核过来源（`tools/_p618`）
>
> 索引 `outputs/` **1,696 个归档文件 / 15,007,369 字符**，逐条核对 README 引用的统计量：
> `5048`/`1478`/`1563`/`1900`/`0.0055`/`5968`/`2842`/`0.5826`/`0.2057`/`-1468`/`-757`/`0.100`/`98.9`
> —— **13/13 全部在归档里有字面匹配** ✅
> （**并注明该检查的限度**：字面匹配只证明数字存在，不证明归因正确；更强的门禁是稿件自己的 claim ledger。）
>
> **项目门禁同时复核**：`python tools\\_claim_ledger.py --apply` ⇒ **✅ 通过 80 ｜ ❌ 失败 0 ｜ 共 80 条**。
>
> ### 五、🔴 顺带发现：**两处身份仍在 git 历史里**
>
> | 位置 | 身份 | 来源 |
> |---|---|---|
> | 本仓库 `git config`（**本地**） | `Hongrui Wan <2024282101@hrbeu.edu.cn>` | 一直如此；我此前的 6 次提交也用它 |
> | 操作者在 GitHub 网页改的 2 次提交 | `MoYUYao666 <hongrui998@outlook.com>` | **网页编辑用 GitHub 账号的邮箱** |
>
> **已处置**：把**本仓库**（`publish_clean/`）的提交身份改为中性
> **`Repository Maintainer <noreply@example.com>`**（**未动全局配置**）。
> **⇒ 但从下一次提交起才生效；历史里的旧身份仍在。**
>
> **⇒ 若仓库将公开，历史需一并处理**（与之前记录的 `docs/` 历史同批）：
> ```bash
> git filter-repo --path docs --invert-paths \\
>   --email-callback 'return b"noreply@example.com"' \\
>   --name-callback  'return b"Repository Maintainer"'
> git push --force
> ```
> **⇒ 若暂不公开（当前 `isPrivate: true`），可先不动** —— Zenodo 归档的是 release 快照，快照里没有作者身份信息。
>
> ### 六、状态
>
> | 项 | 结果 |
> |---|---|
> | 提交 | **`c42c6e8`**（合并提交，含操作者的 `363fcbd`/`0dfdd67`） |
> | 推送 | ✅ `0dfdd67..c42c6e8` |
> | tag | 已重打到 `c42c6e8` |
> | Release | 已重建：`isDraft: false`、`Latest` |
> | 远端 README | **5,619 字符 / 126 行**，个人信息 0、其它论文 0 |
>
> **Release**：https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v1.0-prl-revision
>
> ### 七、剩余
>
> ① **仓库改公开 ⇒ 拿 Zenodo DOI ⇒ 填三处（稿件 Data statement / cover letter / EM 表单）⇒ 重编译重传**
> ② **git 历史里的身份与 `docs/`**（若公开则需 `filter-repo`）
> ③ **许可**：库里无 LICENSE ⇒ README 已明示"未授予许可"；**若要开源需你定许可类型**
> ④ `p3d_summary.json` 指纹更新（非阻塞）⑤ EM 三个回复框 ⑥ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "README 重写为「只有 Paper 3" in t:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("README 重写为「只有 Paper 3", "c42c6e8", "hongrui998@outlook.com", "Repository Maintainer", "13/13"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
