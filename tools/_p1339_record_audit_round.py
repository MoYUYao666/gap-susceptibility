# -*- coding: utf-8 -*-
r"""Record the audit round of 2026-10-19: findings, fixes, verdicts.

    python tools/_p1339_record_audit_round.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **🧪 2026-10-19 13:55 —— 升级包审核轮：查出并修掉 3 处真问题；两稿仅剩"冻结包 vs 本地修订稿"预期差异**
>
> 用 `paper-audit` 模式对 **A1（a1_paa）**、**Paper A（paperA_nc / paperA_springer）** 各跑一遍 86 项注册表：
>
> | 稿件 | 首轮 | 修复后 | 剩余 |
> |---|---|---|---|
> | A1 | BLOCKED（I-02）| **仅 I-02**（冻结包 58 页 vs 本地 60 页）| 预期差异，已文档化 |
> | Paper A / NC | BLOCKED（B-04 overfull、F-04/F-05 门禁、F-09 cover letter 页数、I-02）| **仅 I-02** | 预期差异 |
> | Paper A / Springer | BLOCKED（F-04/F-05）| ✅ **READY grade A**（pass=53 fail=0）| — |
>
> **真问题与修复**：
> 1. **Table 7（Fit Diagnostics）过宽**（右侧被切，10.1 pt overfull）→ 改 `\\footnotesize` + `\\tabcolsep=4pt` + 缩短表头/“full FT”，overfull 归零；
> 2. **cover letter 声称 70 页**（本地稿已 72 页）→ `cover_letter_nc.tex`/`cover_letter.tex` 改为 72 页并重编，`_p1181` 一致性 gate 从 2 failure → **0 failure**；
> 3. **paperA 审计门禁期望值过期**（ledger 已 88 条，profile 仍写 "PASS 76"）→ 更新为 `PASS 88`；
> 4. 顺带：Paper A 新增示意图补 `\\ref{fig:site_schematic}`（消除 C-05/C-07 中的死标签）。
>
> **门禁**：A1 ledger **179/179**、Paper A ledger **88/88**、主 ledger **96/96**；A1 冻结件 **16 件核验未变**。
> **结论**：两稿正文无待修缺陷；剩下的 I-02/I-06 是"投出版 PDF 冻结、本地稿继续升级"的**预期状态**，任何替换都必须先有编辑部决定。
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
    if "升级包审核轮" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("105. 🧪 **升级包审核轮（2026-10-19 13:55）** —— paper-audit 三 profile：A1 与 Paper A-NC 仅剩**预期** I-02（冻结包 vs 本地修订稿），"
           "**Paper A-Springer READY/A**；修掉 Table 7 过宽（overfull）、cover letter 页数（70→72，gate 0 failure）、审计门禁期望值（PASS 76→88）"
           "与示意图引用；三台账 179/179、88/88、96/96；A1 冻结件 16 件未变。\n")
    if "升级包审核轮" not in m:
        anchor = "104. 🚀 **升级包 14 项执行完成"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
