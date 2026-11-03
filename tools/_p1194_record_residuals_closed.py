# -*- coding: utf-8 -*-
r"""Record the closure of the last four residual items.

    python tools/_p1194_record_residuals_closed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "docs" / "PAPERA_REVISION_SPEC.md"
P3DOC = REPO / "docs" / "P3_AUDIT_10PP_2026-10-17.md"
HANDOFF = REPO / "HANDOFF.md"

SPEC_NOTE = """
> **✅ 2026-10-17 23:45 —— §7.1 剩余项中的三条已结案（原文保留作历史）**
>
> | 原"待核"项 | 结论 | 证据 |
> |---|---|---|
> | SigLIP CGΔ（旧记 +0.067 / +0.058）| **不是缺归档，而是旧稿残句**。现稿引用的 SigLIP 严格冻结行是 `+0.0664 / −0.0114 / +0.0522`，由 `outputs/siglip_strict/seed{42,123,456,789,1024}/` 的 **r=8 五 seed** 精确复现（R@1 亦为 `0.432 / 0.619 / 0.341`）；r=4 是另一批扫描，不属该行 | `tools/_p1192_verify_siglip_row.py` → `outputs/analysis/siglip_row_verify.json`（`reproduces: true`）|
> | `k = 0.043`（\\|g_v\\| 对 rank 斜率）| **已不在稿件**：全稿 `0.043` 仅两处，分别是 COCO rank-8 的 CGΔ `−0.043` 与 COCO 严格冻结的 `−0.0430`，与该斜率无关 ⇒ 无"无源数字"可清 | 全稿 grep（`paper合/sections/*.tex`）|
> | `yi2025decipher` 的 "ICML 2026 version" | **无据，已删**：arXiv `2510.03268`（2026-10-17 查询）标题与作者与 bib 完全一致，元数据无任何 ICML 信息；note 字段移除后重编译 | MCP arXiv 元数据；`paper合/references.bib` |
>
> 另：`empirical.tex` 的 −0.064 vs −0.032 属**两种协议**的差（legacy vs 严格冻结），已在 `tab:position` 表注与正文披露，
> 保持原样；"重合 227 词"为该扫描口径的地板，不再改。
"""

P3_NOTE = """
## Post-fix 之二：label 警告清零（2026-10-17 23:45）

- `cor:retrieval-specialization` 与 `thm:repr` 实际在 `sections/appendix.tex` 有引用，而 10 页版**不含附录** ⇒ 旧判定必然报警；
  审计改为**全树判定**（`*.tex` + `sections/` + `sections_full/` + `supplementary/`）。
- `cor:phase-transition` 与 `def:gap-susceptibility` 全树无引用 ⇒ 作为死 label 删除。
- 重建：`main.pdf` 10 页、`main_10pp.pdf` 10 页、`main_full.pdf` 13 页；`audit_check.py` 与 `audit_pdf.py` 均
  **0 hard failure / 0 warning**。
"""

ENT = """> **✅ 2026-10-17 23:45 —— 最后四项遗留全部结案（无新实验需求）**
>
> 操作者要求"全做，补实验"。核查后发现**两项"待核"根本不需要补实验**，因为数字要么已被现稿弃用、要么已精确可复现：
>
> ### 一、SigLIP CGΔ：**不是缺归档，是旧稿残句**
> 现稿引用的是严格冻结行 `+0.0664 / −0.0114 / +0.0522`，由 `outputs/siglip_strict/seed{42,123,456,789,1024}/`
> 的 **r=8 五 seed** 精确复现（R@1 `0.432 / 0.619 / 0.341` 也一致）；`r=4` 属另一批扫描，不并入。
> 旧记的 `+0.067 / +0.058` 来自 P1 草稿，**现稿已不引用**。脚本 `tools/_p1192_verify_siglip_row.py`
> ⇒ `outputs/analysis/siglip_row_verify.json`（`reproduces: true`）。
> ⚠️ 途中我自己踩过一次：首次分组把 r=4 与 r=8 混算（n=10）得出"不匹配"，按 rank 分开后三臂全中。
>
> ### 二、`k = 0.043`：**已不在稿件**
> 全稿 `0.043` 仅两处（COCO rank-8 的 CGΔ、COCO 严格冻结的 −0.0430），与该斜率无关 ⇒ 无"无源数字"可清，无需重跑。
>
> ### 三、`yi2025decipher` 的 "ICML 2026" 括注：**无据，已删**
> arXiv `2510.03268` 元数据（2026-10-17 查询）标题/作者与 bib 一致，**无任何 ICML 信息** ⇒ 移除 note 字段，
> 重跑 bibtex。Paper A 重建：NC **70 页** / Springer **50 页**（0/0/0），投稿包独立编译 **70 页一致**，台账 **76/76**、**96/96**。
>
> ### 四、P3 label 警告清零
> `cor:retrieval-specialization` / `thm:repr` 在 `sections/appendix.tex` 有引用，而 10 页版不含附录（旧判定误报）⇒
> 审计改为**全树判定**；另两枚 `cor:phase-transition` / `def:gap-susceptibility` 全树无引用 ⇒ 作为死 label 删除。
> P3 重建：main 10 / main_10pp 10 / main_full 13 页，**两个审计脚本均 0 hard failure / 0 warning**。
>
> **结论：本轮无新实验需求**——两项"待核"都不是数据缺口；若将来要把 SigLIP 的 r=4 扫描也纳入正文，那才需要新分析。
>
> 脚本：`_p1192`（SigLIP 复算）｜`_p1193`（bib note + P3 审计/label）｜`_p1194`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    s = io.open(SPEC, encoding="utf-8").read()
    if "§7.1 剩余项中的三条已结案" not in s:
        i = s.find("### 8.6 第二轮一致性修复")
        if i < 0:
            print("  !! spec anchor missing")
            return 1
        io.open(SPEC, "w", encoding="utf-8", newline="").write(s[:i] + SPEC_NOTE.strip() + "\n\n" + s[i:])
        print("  spec updated")
    p = io.open(P3DOC, encoding="utf-8").read()
    if "Post-fix 之二" not in p:
        io.open(P3DOC, "w", encoding="utf-8", newline="").write(p.rstrip("\n") + "\n" + P3_NOTE)
        print("  P3 audit doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "最后四项遗留全部结案" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
