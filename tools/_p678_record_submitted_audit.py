# -*- coding: utf-8 -*-
r"""Record the audit of the submitted PDF in the handoff document.

    python tools/_p678_record_submitted_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-14 17:30 —— 核验操作者**已提交的修订稿**（`PRLETTERS-D-26-02378_R1.pdf`，33 页）：**当前版本，未传错**
>
> ### 一、核验对象
>
> 操作者提供的 `C:\\Users\\hongr\\Desktop\\PRLETTERS-D-26-02378_R1.pdf`：
> **33 页 / 2,997,481 字节 / 150,922 字符**（EM 生成的合并包，非单篇）。
>
> ### 二、✅ 真实结构（由 EM 注释读出，非推测）
>
> EM 在每份附件前打了来源标记（`Click here to access/download; <slot>; <file>`）：
>
> | 页 | 槽位 / 内容 | 判定 |
> |---|---|---|
> | 1 | EM 记录页（新标题 + 新摘要） | ✅ |
> | 2–4 | Cover letter + Authorship Confirmation + 声明 | ✅ |
> | **5–15** | **`slot=Manuscript`，`manuscript.pdf`** = **2026-10-12 原投稿** | ℹ️ **EM 自动附上原稿供对照，属正常** |
> | 16–18 | `slot=Figure` ×3（fig1/2/3） | — |
> | 19 | `slot=Supplementary material` = `P3_PRL…_Supplementary.pdf` | ✅ 新件 |
> | 20 | `slot=LaTeX source files` = `P3_PRL…_LaTeX_Source.zip` | ✅ **新包（227,864 字节）** |
> | **21–30** | **「Revised manuscript (marked up)」= 修订稿** | ✅ **当前版本** |
> | 31–32 | Highlights + Declaration of competing interests | ✅ |
>
> ### 三、✅ 修订稿与本地 `main.pdf` **逐标记一致**
>
> | 标记 | 提交件(21+) | 本地盘 | 原稿(5–15) |
> |---|---|---|---|
> | 新标题（不折行） | ✅ | ✅ | ❌ |
> | Zenodo DOI `23341223` | ✅ | ✅ | ❌ |
> | **6-seed 值** `2344` / `1477` | ✅ | ✅ | **❌** |
> | **3-seed 旧值** `3607` / `2241` | **无** | **无** | 无 |
> | 旧标题 | **无** | **无** | **有** |
> | 旧单位 `School of Electronics and Computer Science` | **无** | **无** | **有** |
> | `5048`、`0.0055`、`R3`、`additivity`、`largest caveat` | ✅ | ✅ | — |
>
> **⇒ 结论：提交进去的修订稿就是 10-13 那一版，没有把旧稿当成新版传。**
>
> ### 四、⚠️ 我先前的两次**误判**（已修正，记录下来防重犯）
>
> | # | 我的初判 | 实际 |
> |---|---|---|
> | 1 | "第 5 页那份旧稿被传成了 Manuscript ⇒ 传错槽位" | **错**。第 5 页的 `Manuscript` 槽位放的就是**原投稿**，**EM 的合并包会自动带上原稿供对照**；修订稿在 21 页起。**槽位全部正确。** |
> | 2 | "修订稿第 21 页仍出现 `unique admissible` ⇒ 撤回了还留着" | **错**。那两处**都被 R3′ 限定**：<br>· `…the answer the allocation problem permits: **under five requirements the problem imposes**, Γ = ⟨∇E, u⟩ is the unique admissible statistic up to positive scaling`<br>· `…is the unique admissible statistic **subject to (R3′)**`<br>**⇒ 这正是修订后的正确写法**（撤回的是"仅凭 R1–R5 就唯一"）。 |
>
> **⇒ 教训：判"某措辞是否构成问题"必须看整句限定语，不能只搜关键词字面。**
>
> ### 五、✅ 顺带核实：页数
>
> 盘上 `main.pdf` 文本切出 11 段，其中**第 11 段 0 字符**（`pdftotext` 的尾部换页符），
> **有效页 = 10 页** ⇒ 与记录一致，**未超页**。
>
> ### 六、状态
>
> - **修订稿已提交**（`PRLETTERS-D-26-02378R1`），文件槽位正确、内容为当前版本
> - **剩余（操作者侧）**：① Funding Information 字段（建议不勾 "not available"，见 HANDOFF 上一条）
>   ② 确认 Data statement 下拉用了 `Other` + 200 字符说明 ③ 等编辑部处理
> - **我们侧**：无阻塞项
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "核验操作者**已提交的修订稿" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("核验操作者**已提交的修订稿", "未传错", "两次**误判", "R3′", "有效页 = 10 页"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
