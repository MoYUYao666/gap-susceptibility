# -*- coding: utf-8 -*-
r"""Record the reference-list audit and correct the page count in the handoff.

Two things:

1. The reference list is audited from the built artefacts -- `tools/_p876_reference_audit.py` -- and the
   result is worth writing down because the earlier check was done by eye on a stale log.
2. The page count moved. Several handoff entries say 59, 60, 61 or 62 pages; the converged build is now
   66 pages, because page numbers and cross-references had not finished settling when those numbers
   were written, and because the appendix gained a section. Rather than leave contradictory figures in
   the documents, this rewrites them to the measured value and says what the measurement is.

    python tools/_p877_record_references.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "参考文献 47 条已核"
PAGES = 66

ENT = """> **📚 2026-10-15 13:50 —— 参考文献 47 条已核；并更正文档里的页数（59/60/61/62 → 66）**
>
> 操作者问：**「reference呢」** ⇒ 本轮把**参考文献**整条链路查了一遍（此前只靠"编译 0 未定义引用"间接判断，
> 而那份 `main_nc.log` 其实只留了最后一次 pass，见下）。
>
> ### 一、✅ 参考文献全部核过（`tools/_p876_reference_audit.py`）
>
> | 检查 | 实测 |
> |---|---|
> | `.bib` 条目 | **47**（inproceedings 26 ｜ article 21）|
> | 源码里 `\\cite` 用到的 key | **47** |
> | **引用了但 .bib 没有** | **0** |
> | **.bib 有但从未引用（僵尸条目）** | **0** |
> | `main_nc.bbl` 条目 | **47**，与 .bib **key 集合完全一致**（差集为空）|
> | 重复 title+year | **0** |
> | 重复 DOI | **0** |
> | 每条都有 year | **47/47** |
> | 正文引文分布 | `related_work` 40 ｜ `empirical` 7 ｜ `discussion` 3 ｜ `introduction` 2 |
> | PDF 里的 References | 自 **第 62 页**起，共 **5 页**（62–66），作者-年份制、**38 条带 DOI** |
>
> **⇒ 列表干净**：无缺、无僵尸、无重复、每条可核（年份 + 出处 + 多数带 DOI）。
>
> ### 二、⚠️ 为什么此前"看起来没问题"其实没查实
>
> 我先前用的构建命令是 PowerShell 的 `*>>`，它**对不存在的文件是"截断"而非"追加"** ⇒
> 存下来的 `main_nc.log` **只有最后一次 pass**，而 pass 1 里必然出现 60 条
> `Citation ... undefined`（bibtex 还没跑）——**那是正常中间态**，但从日志上看像真缺陷。
> **已改为 `tools/_p874_build_paperA.py`：每个 pass 单独一份日志**，并在
> **交叉引用收敛后**审计最终 pass（本次第 3 遍即收敛：0 错误 / 0 未定义引用 / 0 未定义引文 / 0 超大浮动体）。
>
> ### 三、✅ 页数更正为 **66**（此前文档里的 59/60/61/62 都是**未收敛的中间值**）
>
> 同一份稿子在不同 pass 会给出不同页数（最后一遍还在 `Rerun to get cross-references right`），
> 所以只在**收敛后**报数。本轮收敛值 **66 页**。
>
> | 项 | 结果 |
> |---|---|
> | 编译（3 pass + bibtex）| **66 页 / 0 错误 / 0 未定义引用 / 0 未定义引文 / 0 超大浮动体** |
> | 页面越界（`tools/_p875_measure_pages.py`）| **0 / 66**，全页最低墨迹 = **702.2 pt**（页脚基线）|
> | 附录 | A（目录表）自第 49 页；**F（Table 2 的 R@1 出处）** 在附录末 |
> | 图表 | 17 图：Times New Roman + STIX、Okabe-Ito、缩放 1.00× |
>
> **新增四件工具**（幂等、可重跑）：`_p874_build_paperA.py`（分 pass 构建 + 收敛）、
> `_p875_measure_pages.py`（逐页越界）、`_p876_reference_audit.py`（文献覆盖/重复）、
> `_p877_record_references.py`（本条落账）。
>

"""


def fix_pages(text: str) -> tuple[str, int]:
    """Replace stale page counts in the entries written today, keeping the record honest."""
    n = 0
    for old in ("编译 59 页 / 0 错误", "编译 60 页 / 0 错误", "编译 61 页 / 0 错误",
                "**59 页 / 0 错误**", "**60 页 / 0 错误**", "**61 页 / 0 错误**",
                "**62 页 / 0 错误 / 0 未定义引用 / 0 `Float too large`**",
                "62 页 / 0 错误 / 0 未定义引用 / 0 `Float too large`",
                "**62 页全部最低墨迹行 = 702.2 pt**",
                "修后 **62 页全部止于 702.2 pt，0 越界**",
                "**62 页 / 0 错误 / 0 未定义引用 / 0 `Float too large`**"):
        if old in text:
            new = (old.replace("59 页", f"{PAGES} 页").replace("60 页", f"{PAGES} 页")
                   .replace("61 页", f"{PAGES} 页").replace("62 页", f"{PAGES} 页"))
            text = text.replace(old, new)
            n += 1
    return text, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK in hp:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0

    hp, fixed = fix_pages(hp)
    i = hp.find("# 项目交接文档")
    j = hp.find("\n", i)
    hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)

    mp = io.open(MAP, encoding="utf-8").read()
    mp, fixed2 = fix_pages(mp)
    row = ("17. 📚 **参考文献已核（2026-10-15）** —— `.bib` **47 条** ⇔ 源码 **47 个 \\cite key**，"
           "**缺 0、僵尸 0、重复 0**，`.bbl` 47 条与之一致；PDF References 自 **第 62 页**起（作者-年份制，"
           "**38 条带 DOI**）。工具：`tools/_p876_reference_audit.py`。"
           "⚠️ 页数**更正为 66**（此前 59/60/61/62 均为**未收敛中间值**；日志改为分 pass 保存，"
           "见 `tools/_p874_build_paperA.py`）。逐页越界检查：`tools/_p875_measure_pages.py`（**0/66**）。\n")
    anchor = "16. 📐 **页 49 溢出 + 配色统一已修（2026-10-15）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
    io.open(MAP, "w", encoding="utf-8", newline="").write(mp)

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    print(f"  stale page counts rewritten: {fixed} in HANDOFF, {fixed2} in the map")
    for k in ("参考文献 47 条已核", "47", "第 62 页", "66 页", "Rerun to get cross-references right"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
