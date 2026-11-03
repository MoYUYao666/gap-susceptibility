# -*- coding: utf-8 -*-
r"""落账：六项收尾核查（2026-10-14）。

    python tools\_p561_record_six_checks.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📦 2026-10-14 02:00 —— 六项收尾核查：开源要求 / README / 回复覆盖 / 稿件对应 / 上传清单 / 署名**
>
> ### 一、开源与数据要求（Guide 原文，**是硬要求**）
>
> > **Research data deposit, citation and linking**：*For this journal, **Option C** … you are
> > **required** to: **Deposit your research data in a relevant data repository.** Cite and link
> > to this dataset in your article. If this is not possible, make a statement explaining why.*
>
> **⇒ 要求的是「数据入库 + 引用链接」，不是「必须开 GitHub」**（Guide 无此条款）。
> **⚠️ 缺口：我们尚未真正 deposit。** Data statement 已如实写成「派生数据在私有仓库、
> 接受后公开归档」，并声明**分析不需任何非公开数据**。**要完全合规需先 deposit（建议 Zenodo，免费给 DOI）。**
>
> ### 二、✅ GitHub README 已修（它原本在**宣传已撤回的主张**）
>
> | 旧 README | 现况 |
> |---|---|
> | *"$\\Gamma$ is the **unique** admissible … statistic"* | 改为**需 R3$'$ 公理**（含反例） |
> | *"Alignment **phase transition** at $r_c\\in[5,6]$"* | 改为**bracketed**，且**不主张架构依赖** |
> | *"reduces uncertainty by **$32\\times$**"* | **删除** |
> | *"**181 runs**"*、计数表 | 改为 **126 + 57 runs** |
> | *"**Prepared for IEEE TNNLS**"* | 改为**已投 PRL（Revise）** |
> | 缺硬件/引用/数据可用性 | **新增四节**：Hardware and environment（RTX 4060 8GB / A800 / CPU 后端差异 0.09%）、Data availability、Citation（BibTeX）、License |
>
> **⇒ README 3,527 → 6,090 字符 / 133 行**；`unique` / `32×` / `sharp 相变` / `TNNLS` / `181` **残留全部 0**。
>
> ### 三、✅ 三项复核
>
> | 项 | 结果 |
> |---|---|
> | **回复覆盖** | **33/33**（三份：4 / 5 / 23 个 Point，各有等量 Response） |
> | **稿件已对应修改** | 14 项关键词全部命中（R3$'$ 13 处、反例 4 处、$7{,}237{,}632$ 3 处、$3.09\\times$ 1 处、bracketed 9 处、AdaLoRA 8 处、126 runs 2 处…） |
> | **全仓库断头命令** | **修 32 处**（`sections_full/` 26 处 + `title_page_prl.tex` 等）⇒ **残留 0** |
>
> ### 四、✅ 署名已改（操作者要求）
>
> **去掉 `School of Electronics and Computer Science`** ⇒ `main.tex` / `main_full.tex` /
> `supplementary.tex` / `main_10pp.tex` / `title_page_prl.tex` **五处**已改；
> **保留** `University of Southampton` + 地址 + **邮箱**（Guide 要求邮箱必须出现在首页脚注）。
> 已投出的 `SUBMISSION/P3_PRL/` **不动**（历史存档）。
>
> ### 五、✅ 上传清单已生成（`UPLOAD_CHECKLIST.md`）
>
> - **重新上传 4 项**：`main.pdf`（10 页）、**LaTeX 源**（12 文件）、cover letter（**需先补篇幅说明**）、
>   **Authorship Confirmation**（**必须作为 item type `Cover Letter`，否则 AUTOMATIC REJECTION**）
> - **新上传 2 项**：`supplementary.pdf`（5 页）、**三个回复框**（EM 表单填写）
> - **建议更新 1 项**：`highlights.pdf`（现版含**已撤回主张**）
> - **❌ 不上传**：`main_full.pdf`（非投稿件）、`evidence/`、`reviews/`
>
> **LaTeX 压缩包：要上传** —— Guide 明确 *"A PDF is not an acceptable source file"*；
> 已打包 `manuscript/P3_latex_source_revision.zip`（**12 个文件 / 45 KB / testzip 通过**）。
>
> ### 六、状态
>
> - **投稿件**：**10 页 / 0 错误 / 0 未定义**｜**补充材料 5 页**｜**完整版 13 页**
> - **修订包** 33 个文件（含 `UPLOAD_CHECKLIST.md` 与 LaTeX zip）
> - **剩余**：① 操作者决定**是否 deposit 数据**（Option C 的唯一实质缺口）
>   ② 更新 cover letter / title page / highlights 的 PDF ③ EM 表单填三个回复框 ④ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "六项收尾核查" in t:
        print("  已记录")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("六项收尾核查", "Option C", "P3_latex_source_revision.zip", "AUTOMATIC REJECTION", "School of Electronics"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
