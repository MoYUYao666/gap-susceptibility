# -*- coding: utf-8 -*-
r"""落账：两份稿子最终过一遍（2026-10-11 晚）。

    python tools\_docs_final_pass.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📋 2026-10-11 晚 —— 两份稿子最终过一遍：查出并修 3 个问题；投稿包重建**
>
> ### 一、`paper合`：查出 **1 处论文自相矛盾**（真错）
>
> | 位置 | 说法 | 判定 |
> |---|---|---|
> | `tab:position_strict` 表注 | *"Patch size **does not separate** the groups"* | ✅ 已修正 |
> | **`empirical.tex` 一段** | *"the ordering is a property … of **the patch size** the encoder uses"* | 🔴 **旧归因残留** |
> | 同文件另一段 | *"That reading **does not survive** the matched comparison … we therefore report the grouping … **rather than as a property of patch size**"* | ✅ 已修正 |
>
> **→ 同一篇里三处口径不一。** 已改为与表注一致：*"the ordering follows the **pre-training
> objective** rather than vision-language adaptation in general"*（并保留 CLIP B/16 与 B/32 同秩同序的证据）。
>
> ### 二、`paper合`：**投稿包过期**（真问题）
>
> `NC_submission/latex_source/sections/` 里 **4 个副本停在 10-05/10-06**（`empirical`/`validation`/
> `supplement`/`discussion`），而它们已在 10-11 大改 → **`Manuscript.pdf` 与 `latex_source.zip` 都是旧稿**。
>
> **已重建**（`tools/_p189` + `_p190` + `_p197`）：
>
> | 件 | 结果 |
> |---|---|
> | `Manuscript.pdf` | **56 页，0 错误，0 未定义引用** |
> | `latex_source.zip` | 43 个文件，1.91 MB |
> | `Cover Letter.pdf` | 从**新版通用 cover letter** 派生（`cover_letter_nc.tex`）→ 三者哈希一致 |
> | 哈希核对 | `empirical`/`validation`/`supplement`/`discussion`/`main_nc`/`references.bib` **全部一致** ✅ |
> | `README.md` | 更新：49→**56 页**；244→**246 词**；41→**47 条**文献；并记录数据口径与审计结果 |
>
> ### 三、`paper合`：Cover Letter 有 **6 处过期**（已重写）
>
> | # | 旧版 | 问题 |
> |---|---|---|
> | 1 | *"49 pages"* | 实为 56 |
> | 2 | *"abstract of 238 words"* | 实为 246 |
> | 3 | *"ordering tracks the encoder's **patch size** without exception"* | 🔴 **已被论文明文否证** |
> | 4 | *"ODE … mean $R^2=0.986$"* | 论文写 **0.949**（`0.986` 是别人工作的数字，被误抄） |
> | 5 | *"seven strict-freezing configurations"* | 现口径：三个对比式 + 两个其它目标骨干 |
> | 6 | 披露：*"A predecessor manuscript under review at PR (Protect, Don't Perturb…)"* | 那份稿**已合并进本文** → 改为 *"**supersedes** it"* |
>
> **新版另加**（本轮新发现）：**数据集翻转**（Flickr30k `text_only` / MS-COCO `both`，各 5 seed 同批次）、
> **两处理论否证**、**解码器 VLM 13 seed**、以及 **4-bit 不可复现**的如实披露。
>
> ### 四、A1：最终检查
>
> | 项 | 结果 |
> |---|---|
> | 六份投稿件 | ✅ 旧标题/旧刊名/旧邮箱 **0 残留** |
> | 摘要 | ✅ **245 词**（限 250） |
> | 关键词 | ✅ **5 个**（限 1–6） |
> | Highlights | ✅ **5 条**，最长 68 字符（限 3–5、≤85） |
> | 文献 | ✅ **56 条**，全带 label（APA） |
> | PDF | ✅ main 41｜cover_letter 2｜declaration 1｜highlights 1｜abstract 1 页，**全部最新** |
>
> **我上一版检查脚本曾误报"关键词 0 个"**——因 A1 用的是 `\\begin{keyword}` 环境（单数），
> 而我只搜 `\\keywords{}`；已修（`tools/_p188`）。
>
> ### 五、编译总表
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | `paper合` Springer | **41**（原 40，patch-size 修正 +1） | 0 | 0 | 0 |
> | `paper合` NC | **56** | 0 | 0 | 0 |
> | **投稿包** `Manuscript.pdf` | **56** | 0 | 0 | — |
> | A1 `main` | **41** | 0 | 0 | 0 |
>
> ### 六、最终检查清单（`tools/_final_review.py`）
>
> ```
> A1：6 份干净 ｜ 摘要 245 ｜ 关键词 5 ｜ highlights 5 ｜ 文献 56 ｜ PDF 全最新
> paper合：门禁 80/80 ｜ 统计审核 20/20 ｜ 旧数字残留 0 ｜ Springer 41 页 ｜ NC 56 页
> 检查结论：✅ 全部通过
> ```
>
> ### 七、结论
>
> **两份稿子现在都处于可投状态**：
> - **A1** → 等操作者点 ATS 链接选 `Neural Networks`（截止 `Nov 08`）
> - **`paper合`** → 等操作者定目标刊（候选 ESWA / KBS / CVIU）；投稿包已按 **Neurocomputing** 模板备好
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "两份稿子最终过一遍" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("两份稿子最终过一遍", "自相矛盾", "投稿包过期", "**41**（原 40",
              "supersedes", "0.949", "keyword"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
