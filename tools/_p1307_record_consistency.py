# -*- coding: utf-8 -*-
r"""Record the cross-artefact consistency check and its three repairs.

    python tools/_p1307_record_consistency.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **🔎 2026-10-18 22:50 —— 全链路一致性总检：稿件/包/台账/文档/镜像清单已对齐（修 3 处）**
>
> 用 `tools/_p1305_consistency_check.py` 跨五层核对：
>
> | 层 | 结果 |
> |---|---|
> | 稿件 vs 包 | **live main.pdf 54 页 == 包内 Manuscript.pdf 54 页**；Title Page / Cover Letter / Graphical Abstract 逐文件哈希一致 |
> | 源码 zip | 21 条目，`main.tex` 与 live **逐字一致**，figures 18 个（含裁边版） |
> | 台账 | A1 **112/112**、主 **96/96**、Paper A **76/76**，且均比稿件源新（J-01 无告警） |
> | 文档 | `哪篇是哪篇`/`AUTOMATION_HANDOVER`/`SUBMISSION/README`/包 README 无过期数字（HANDOFF 与文件地图里的 53/55 页仅存在于**带日期的历史条目**，按"追加不重写"保留）|
> | 镜像清单 | `_p1284` 已补齐 4 个新归档 + 4 个新脚本 |
>
> **修掉的 3 处不一致**：① 包 README 把揭示函写成 "2 pages"（实为 1 页）→ 模板改为**自动量页数**；
> ② 公开镜像 staging 清单缺 `a1_matched_gap_dense/real_checkpoint_pairs/lower_bound_constants/margin_mass` 及 `_p1299–_p1302` → 已补；
> ③ `AUTOMATION_HANDOVER.md` 仍写 A1 包"51 页" → 改为 **54 页 + 台账 112/112**。
>
> 终检：`PROBLEMS: none`；审计 `a1_paa` **READY grade A：pass=61 fail=0 warn=0**。`_p1305` 可随时重跑复核。
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
    if "全链路一致性总检" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("93. 🔎 **全链路一致性总检（2026-10-18 22:50）** —— `_p1305` 跨五层核对：稿件/包页数一致、源码 zip 最新、"
           "三台账 112/96/76 且不过期、文档无过期状态、镜像清单补齐；修 3 处（包 README 揭示函页数、镜像清单缺件、"
           "AUTOMATION 51→54 页）。终检 PROBLEMS: none，审计 READY/A。\n")
    if "全链路一致性总检" not in m:
        anchor = "92. 🧭 **新颖性 (a) 下界"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
