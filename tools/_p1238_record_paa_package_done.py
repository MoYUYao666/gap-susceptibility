# -*- coding: utf-8 -*-
r"""Record the completed A1 PAA package and the final audit state for both manuscripts.

    python tools/_p1238_record_paa_package_done.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
VENUE = REPO / "docs" / "A1_VENUE_DECISION.md"

SEC = """

### 13.3 PAA 投稿包已建成（2026-10-18 15:25）

`paper_a1/PAA_submission/`（独立编译验证：**45 页、0 错误 / 0 未定义**，与主文件页数一致）

| 文件 | 大小 | 说明 |
|---|---|---|
| `Manuscript.pdf` | 835,785 B | **45 页**，elsarticle review 格式 |
| `Title Page.pdf` | 105,577 B | **1 页**，标题/单位/通讯作者 + 完整 Declarations |
| `Cover Letter.pdf` | 127,246 B | **1 页**，披露三次前投史与相关在审稿 |
| `latex_source.zip` | 741,640 B | **14 文件**（main.tex、related_work.tex、title_page.tex、figures/）|
| `README.md` | 961 B | 上传对照 + PAA 合规表 |

**同时修掉一处硬缺陷**：`main.tex` 的 `\\journal{Neural Networks}` 仍是旧刊名，已改为 `\\journal{Pattern Analysis and Applications}`。

**揭示函披露内容**：① 本文三次前投未中（PRL `PRLETTERS-D-26-01941` 有外审；Neurocomputing `NEUCOM-D-26-20952`
桌面拒；Neural Networks `NEUNET-D-26-09426` 桌面拒、AE 判新颖性边际）；② 相关在审稿（PRL Commentary
`PRLETTERS-D-26-02402`）与"companion manuscript 另行处理"；③ 未一稿多投、数据与 AI 使用见 title page。
⚠️ 其中"companion manuscript 另行处理"一句为**中性表述**；若 Paper A 已实际投出，可按需改为"under consideration at …"。

**审计**：新建 `a1_paa` profile（PAA 政策：摘要 150–250、关键词 4–6、Springer 声明子项、package 映射），
终审 **READY grade A：pass=61 fail=0 warn=0 manual=9 skip=16**。
同轮 `paperA_nc`：**READY grade A：pass=65 fail=0 warn=2**（警告为既有人工项）。
Neural Networks 冻结包 `SUBMISSION/A1_NeuralNetworks/` 的 16 个文件校验未变。
"""

ENT = """> **✅ 2026-10-18 15:25 —— A1 的 PAA 投稿包建成并通过终检；两篇审计均 READY/A**
>
> **包**（`paper_a1/PAA_submission/`，独立编译 45 页 0/0）：`Manuscript.pdf` 45 页、`Title Page.pdf` 1 页
> （含完整 Declarations）、`Cover Letter.pdf` 1 页（披露三次前投史 + 相关在审稿）、`latex_source.zip` 14 文件、`README.md`。
>
> **顺带修掉硬缺陷**：`\\journal{Neural Networks}` 仍是旧刊名 → 改为 `\\journal{Pattern Analysis and Applications}`。
>
> **新建 `a1_paa` 审计 profile**（摘要 150–250、关键词 4–6、Springer 声明子项、包映射），终审
> **READY grade A：pass=61 fail=0 warn=0**；`paperA_nc` 同轮 **READY grade A：pass=65 fail=0 warn=2**。
> NN 冻结包 16 文件未变。
>
> ⚠️ 一个待你确认的措辞：揭示函中"companion manuscript is being handled separately"为中性表述；
> 若 Paper A 已投出，建议改为"under consideration at Neurocomputing"。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    v = io.open(VENUE, encoding="utf-8").read()
    if "13.3 PAA 投稿包已建成" not in v:
        io.open(VENUE, "w", encoding="utf-8", newline="").write(v.rstrip("\n") + SEC)
        print("  venue doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 的 PAA 投稿包建成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("77. ✅ **A1 PAA 投稿包建成 + 两篇终检 READY/A（2026-10-18 15:25）** —— `paper_a1/PAA_submission/`："
           "Manuscript 45 页、Title Page 1 页（Declarations 齐全）、Cover Letter 1 页（披露三次前投史）、源码 14 文件、README；"
           "独立编译 45 页 0/0。修掉 `\\journal{Neural Networks}` 旧刊名。新建 `a1_paa` profile：A1 **pass=61 fail=0 warn=0**、"
           "Paper A **pass=65 fail=0 warn=2**，均 READY/A；NN 冻结包未变。\n")
    if "A1 PAA 投稿包建成" not in m:
        anchor = "76. 🛠️ **新建 `a1_paa` 审计 profile"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
