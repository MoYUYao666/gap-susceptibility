# -*- coding: utf-8 -*-
r"""Backfill the Paper A manuscript number NEUCOM-D-26-23760.

Every status document that said "稿号待补" for Paper A is updated in place, and a dated entry records where the number
came from. Idempotent: running twice changes nothing.

    python tools/_p1323_backfill_paperA_number.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NUM = "NEUCOM-D-26-23760"

EDITS = {
    "HANDOFF.md": [
        ("Paper A → 已投（Submitted，稿号待补）",
         "Paper A → 已投（Submitted，稿号 `" + NUM + "`）"),
        ("**📮 2026-10-18 17:40 —— Paper A 已投出 Neurocomputing（状态 `Submitted`，稿号待补）**",
         "**📮 2026-10-18 17:40 —— Paper A 已投出 Neurocomputing（状态 `Submitted`，稿号 `" + NUM + "`）**"),
        ("> | 稿号 | **待补** —— 该页面暂不显示，需从确认邮件或 EM 作者主菜单取 |",
         "> | 稿号 | **`" + NUM + "`**（2026-10-18 21:30 由操作者提供；此前记“待补”已补全）|"),
    ],
    "哪篇是哪篇.md": [
        ("`paper合/` | **Paper A = P1+P2** ⭐ 当前主稿 | `main_nc.tex` | **Neurocomputing**（elsarticle）｜**2026-10-18 已投出，状态 Submitted**（包 `SUBMISSION/PaperA_Neurocomputing/`；**稿号待补**）",
         "`paper合/` | **Paper A = P1+P2** ⭐ 当前主稿 | `main_nc.tex` | **Neurocomputing**（elsarticle）｜**2026-10-18 已投出，状态 Submitted**，稿号 **`" + NUM + "`**（包 `SUBMISSION/PaperA_Neurocomputing/`）"),
        ("Paper A 于 **2026-10-18** 投 Neurocomputing。",
         "Paper A 于 **2026-10-18** 投 Neurocomputing（稿号 **`" + NUM + "`**）。"),
    ],
    "AUTOMATION_HANDOVER.md": [
        ("（门户状态 Submitted；稿号待补）", "（门户状态 Submitted；稿号 `" + NUM + "`）"),
    ],
    "SUBMISSION/PaperA_Neurocomputing/README.md": [
        ("| 门禁 | Paper A 台账 **76/76 PASS、0 GAP**；主台账 **96/96 通过、0 失败** |",
         "| 门禁 | Paper A 台账 **76/76 PASS、0 GAP**；主台账 **96/96 通过、0 失败** |\n"
         "| 稿号 | **`" + NUM + "`**（Neurocomputing，状态 Submitted，2026-10-18）|"),
    ],
}

HANDOFF_ENTRY = """> **🔢 2026-10-18 21:30 —— Paper A 稿号回填：`NEUCOM-D-26-23760`**
>
> 操作者提供 Neurocomputing 稿号 **`NEUCOM-D-26-23760`**（对应 2026-10-18 17:40 投出的 Paper A，标题
> *Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow Theory for PEFT of Contrastive
> Dual-Encoders*）。所有"稿号待补"的文档已同步：`HANDOFF.md`、`哪篇是哪篇.md`、`AUTOMATION_HANDOVER.md`、
> `文件地图.md`、`SUBMISSION/PaperA_Neurocomputing/README.md`、每周检索提醒 prompt。
>
> 剩余待补：**A1 的 PAA 稿号**（Springer Nature 门户；投稿完成后提供）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for rel, pairs in EDITS.items():
        p = REPO / rel
        t = io.open(p, encoding="utf-8").read()
        for old, new in pairs:
            n = t.count(old)
            total += n if n else 0
            print(f"  {rel}: {n} x {old[:46]!r}")
            if n:
                t = t.replace(old, new, 1)
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(t)
    h = io.open(REPO / "HANDOFF.md", encoding="utf-8").read()
    add_entry = "Paper A 稿号回填：`" + NUM + "`" not in h
    print(f"  handoff new entry needed: {add_entry}")
    if a.apply and add_entry:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(REPO / "HANDOFF.md", "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + HANDOFF_ENTRY + h[j + 1:])
        print("  handoff entry added")
    return 0 if (total or add_entry) else 1


if __name__ == "__main__":
    raise SystemExit(main())
