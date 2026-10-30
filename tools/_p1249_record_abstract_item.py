# -*- coding: utf-8 -*-
r"""Record the standalone Abstract item for Paper A.

    python tools/_p1249_record_abstract_item.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **📄 2026-10-18 16:55 —— Paper A 增加单独 Abstract 文件（Editorial Manager 项）**
>
> 按操作者要求，Paper A 包新增 **`Abstract.pdf`**（1 页）：标题 + 摘要 + 关键词。
>
> | 项 | 值 |
> |---|---|
> | 生成方式 | `tools/_p1247_add_abstract_file.py` 从 `paper合/main_nc.tex` **精确抽取**（原始 LaTeX，不手抄）→ `paper合/abstract_nc.tex` → 编译 → `Abstract.pdf` |
> | 内容校验 | 1 页、0 LaTeX 错误；含标题、`Keywords`、`β / ± / 0.949` 等符号正确渲染；摘要 222–231 词（≤250） |
> | 可复现 | 已并入构建脚本 `_p1169`：重放包构建时输出 `Abstract.pdf <- abstract_nc.pdf`，staged 编译 70 页 0/0 |
> | 包索引 | `SUBMISSION/PaperA_Neurocomputing/README.md` 上传对照新增 `Abstract` 行 |
> | 审计 | `paperA_nc` profile 的 `package_expected` / `package_map` 已登记 `Abstract.pdf`，终审 **READY/A（pass=65 fail=0）** |
>
> 门户上传对照（更新后）：**Manuscript / Abstract / Highlights / Cover Letter / LaTeX source** 五项。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "Paper A 增加单独 Abstract 文件" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("80. 📄 **Paper A 单独 Abstract 文件（2026-10-18 16:55）** —— `SUBMISSION/PaperA_Neurocomputing/Abstract.pdf`"
           "（1 页：标题+摘要+关键词），由 `_p1247` 从 `main_nc.tex` 精确抽取生成；已并入构建脚本可复现；"
           "包 README 与 `paperA_nc` profile 已登记；审计 **READY/A**。\n")
    if "Paper A 单独 Abstract 文件" not in m:
        anchor = "79. 📊 **投稿状态快照"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
