# -*- coding: utf-8 -*-
r"""Record the a1_paa profile and the clean audit.

    python tools/_p1235_record_a1_paa_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **🛠️ 2026-10-18 15:10 —— 新建 `a1_paa` 审计 profile；A1 按 PAA 口径 **READY / grade A（0 失败 0 警告）**
>
> 背景：A1 已从 Neural Networks 改投 **Pattern Analysis and Applications**，而 `a1_nn` profile 要求 NN 专属声明节名
> （`Declaration of competing interest`、`Declaration of generative AI`），按它审会误报 C-09。
>
> 新建 `a1_paa` profile（`tools/paper_audit/profiles.py`）：
> - 限制：摘要 **150–250**、关键词 **4–6**（PAA 原文要求）；
> - 声明：Funding / Competing interests / Ethics approval / Consent for publication / Data and code availability /
>   Authors' contributions / Use of artificial-intelligence tools；
> - 文档：`main.tex` + `title_page.tex`；冻结路径仍指向 `SUBMISSION/A1_NeuralNetworks`（该包必须保持不动）；
> - freeze 基线：`tools/paper_audit/freeze/a1_paa.json`（16 文件）。
>
> **审计结果**：`READY grade A  pass=55 fail=0 warn=0 manual=9 skip=22 error=0`
> （`docs/audits/AUD-a1_paa-20261018T052759Z.md`）。
> PAA 合规：摘要 239 词、关键词 5 个、无正文长度上限、LaTeX 可投、声明合并 + 单独 title page、AI 使用已入 Setup。
> ⚠️ `a1_nn` 仍会报 C-09（NN 声明节名），**那是预期行为**，两套 profile 按目标刊分别使用。
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
    if "新建 `a1_paa` 审计 profile" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("76. 🛠️ **新建 `a1_paa` 审计 profile（2026-10-18 15:10）** —— 按 PAA 政策（摘要 150–250、关键词 4–6、"
           "Springer 声明子项）建 profile 与 freeze 基线（16 文件）。A1 审计 **READY grade A：pass=55 fail=0 warn=0**。"
           "`a1_nn` 仍报 C-09 属预期（NN 专属声明名），两 profile 按目标刊分别使用。\n")
    if "新建 `a1_paa` 审计 profile" not in m:
        anchor = "75. ✅ **A1 按 PAA 规范补齐"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
