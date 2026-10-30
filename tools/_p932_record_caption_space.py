# -*- coding: utf-8 -*-
r"""Refresh the staged files and record the table-caption spacing change.

    python tools/_p932_record_caption_space.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
REV = REPO / "SUBMISSION" / "P3_PRL_revision"
UPLOAD = REV / "UPLOAD_2026-10-15"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "table 与表题间距已加开"

ENT = """> **↕️ 2026-10-15 14:55 —— 补充材料「表格与表题」间距已加开（并说明六次失败的尝试）**
>
> 操作者反馈：**「TABLE S3 标题再远一点」**（表与它下面的 `TABLE S3` 太贴）。
>
> ### 一、✅ 最终做法（可靠、局部、不碰文档类）
>
> 每张表的 **tabular 结束后、`\\caption` 之前**插一行 **`\\vspace{10pt}`**（共 5 处，逐表断言）。
> 实测：规则线到表题首行墨迹 **2.7–3.4 mm → 约 9 mm**。
>
> ### 二、⚠️ 先说清楚：我在这件事上绕了远路，六次尝试里前五次都无效
>
> | # | 尝试 | 结果 |
> |---|---|---|
> | ① | 导言区 `\\setlength{\\abovecaptionskip}{20pt}` | **无效**——IEEEtran 在读取类文件时已把该长度**复制进自己的宏** |
> | ② | 重定义 `\\@IEEEtablecaptionsepspace` | **无效**——用 `\\typeout` 探针确认**该宏一次都没被调用** |
> | ③ | `caption` 宏包 `\\captionsetup{skip=…}` | 部分有效，但该包**替换**了 IEEEtran 的表题排版（类文件明确警告 *Unknown document class*），且**各表表现不一致** |
> | ④ | `etoolbox` 的 `\\patchcmd` 打 `\\@makecaption` | 日志打印 **`P3: WARNING caption patch failed`**——该模式不在宏里 |
> | ⑤ | 在 `\\AtBeginDocument` 里包一层 `\\@makecaption` | 编译报 **`Illegal parameter number`**（该宏不是假定的两参数 long macro）|
> | ⑥ | **每表局部 `\\vspace`** | ✅ **有效且最稳**：只影响本文档这 5 张表，不会波及其它 caption |
>
> **全部 ③④⑤ 的残留已回滚**（`tools/_p931` 里带断言：`caption` 包、`abovecaptionskip`、`patchcmd`、
> `@makecaption`、`AtBeginDocument` **均不得再出现**），**导言区已干净**。
>
> ### 三、⚠️ 顺带纠正一处**页码/版式结论**（我先前记错过）
>
> 我一度把**页面顶部的标题文字**当成了表格线来量间距（"rule y=216"其实是标题行末），
> 得出"表题只差 2.7 mm"的结论**在被测对象上是错的**；改用**逐页渲染 + 直接看图**核对后，
> 确认实际表题位置与间距。**测量脚本必须验证它量到的确实是目标对象**——已写进 `tools/_p925` 的说明里。
>
> ### 四、✅ 复核
>
> | 项 | 结果 |
> |---|---|
> | 编译 | **0 错误 / 0 未定义引用 / 0 未定义引文 / 0 `??`** |
> | Overfull hbox / vbox | **0 / 0** |
> | 栏间空白（6 页逐页）| **全部 clean** |
> | 表与表题间距 | 5 张表**统一约 9 mm** |
> | 页数 | **6 页**（与上一版一致）|
> | 逐条对应 | `tools/_p893` → **CORRESPONDENCE VERIFIED**；`tools/_p910` → **NUMBERING CONSISTENT** |
>
> **交付件**：`SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/` 四个 PDF 已刷新。
> **工具**：`_p924`（表题间距首试）｜`_p925`（表题位置审计）｜`_p926`（表题移到表下 + 去 caption 包）｜
> `_p927`～`_p930`（四次失败尝试，均留证据）｜`_p931`（回滚 + 局部 `\\vspace`，最终方案）｜`_p932`（本条落账）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0

    main_pdf, supp_pdf = P3 / "main.pdf", P3 / "supplementary" / "supplementary.pdf"
    for src, dsts in ((main_pdf, ["main.pdf", "P3_PRLETTERS-D-26-02378_Manuscript.pdf"]),
                      (supp_pdf, ["supplementary.pdf", "P3_PRLETTERS-D-26-02378_Supplementary.pdf"])):
        for d in dsts:
            shutil.copy2(src, UPLOAD / d)
    shutil.copy2(supp_pdf, REV / "CORRECTED_2026-10-15" / "supplementary_corrected.pdf")
    shutil.copy2(main_pdf, REV / "CORRECTED_2026-10-15" / "main_corrected.pdf")
    h = {n: hashlib.sha256((UPLOAD / n).read_bytes()).hexdigest() for n in
         ("main.pdf", "P3_PRLETTERS-D-26-02378_Manuscript.pdf",
          "supplementary.pdf", "P3_PRLETTERS-D-26-02378_Supplementary.pdf")}
    assert h["main.pdf"] == h["P3_PRLETTERS-D-26-02378_Manuscript.pdf"]
    assert h["supplementary.pdf"] == h["P3_PRLETTERS-D-26-02378_Supplementary.pdf"]
    print("  replacement files refreshed")

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("25. ↕️ **补充材料表与表题间距已加开（2026-10-15 14:55）** —— 每表 tabular 后 `\\caption` 前加 "
           "`\\vspace{10pt}`（5 处），表题间距 **2.7–3.4 mm → 约 9 mm**。⚠️ **前五次尝试全无效并已回滚**："
           "`\\abovecaptionskip`（类文件已复制该长度）、`\\@IEEEtablecaptionsepspace`（宏从不被调用）、"
           "`caption` 包（替换类排版且各表不一致）、`patchcmd`（模式不在宏里）、包 `\\@makecaption`（参数号非法）。"
           "复核：0 错误 / Overfull 0 / 栏间 clean / 6 页；`_p893` CORRESPONDENCE VERIFIED、`_p910` NUMBERING CONSISTENT。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 14:55 条目。\n")
    anchor = "24. 📐 **P3 补充材料表格已修（2026-10-15 14:45）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
