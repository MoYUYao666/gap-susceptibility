# -*- coding: utf-8 -*-
r"""Record the revision citation backfill: HANDOFF entry, file-map row, and the three revision documents.

    python tools/_p1327_record_revision_citations.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
A1DOC = REPO / "docs" / "A1_REVISION_REAUDIT.md"
PADOC = REPO / "docs" / "PAPERA_REVISION_SPEC.md"
P3DOC = REPO / "SUBMISSION" / "P3_PRL_revision" / "RELEASE_NOTES.md"

ENT = """> **📎 2026-10-19 12:40 —— 周检引用全部补入本地工作副本（提交包仍冻结）；三稿重编译 0/0/0**
>
> 按"检索到就补上、但**不动已投出的包**"处理，见 `docs/REVISION_CITATION_BACKLOG_2026-10-19.md`：
>
> | 稿件 | 补入 | 位置 | 编译 |
> |---|---|---|---|
> | **A1** | Sharma & Saxena 2026（arXiv:2609.36101）+ Yaras et al. 2024（arXiv:2412.07909），含"几何解释 vs 统计充分性"区分段 | `related_work.tex` + 2 条 bibitem | **59 页**、0/0/0 |
> | **Paper A** | Amblard 条升级为 **IJMI 期刊版**（DOI 10.1007/s13735-026-00423-w）+ CLIP-CIL 两条（Hu 2026 / He 2026）| `sections/related_work.tex` + bib | NC **70 页** / Springer **50 页**、0/0/0 |
> | **P3** | IFCLoRA（2607.22251）/ StatLoRA（2607.20205）/ LoRA-GA²（2608.19800），含"闭式 vs 校准集/搜索"区分段 | `sections/related_work.tex` + bib | **10 页**、0/0/0；`audit_check` 0/0、`audit_pdf` 0/0 |
>
> **冻结状态**：`SUBMISSION/` 三个包一字未动（A1 仍 58 页、P3 R1 哈希不变）。因此 A1 审计出现**预期内**的
> `I-02`（包 58 ≠ 本地 59 页）与 `I-06`（包 README 记 58 页），提交后 `A-01` 消除；这是冻结提交包的正确行为。
> 三台账：**96/96、157/157、76/76** 全过。
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
    if "周检引用全部补入本地工作副本" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")

    m = io.open(MAP, encoding="utf-8").read()
    row = ("101. 📎 **周检引用补录（2026-10-19 12:40）** —— A1 加 Sharma & Saxena 2026 / Yaras 2024（59 页）；Paper A 升级 "
           "Amblard 至 IJMI 期刊版 + 2 条 CLIP-CIL；P3 加 IFCLoRA / StatLoRA / LoRA-GA²（10 页）；三稿 0/0/0、三台账 96/96·157/157·76/76。"
           "**`SUBMISSION/` 冻结未动**（A1 审计 I-02/I-06 为预期差异）。详见 `docs/REVISION_CITATION_BACKLOG_2026-10-19.md`。\n")
    if "周检引用补录（2026-10-19 12:40）" not in m:
        anchor = "100. 📚 **每周文献检索（2026-10-19 12:00）**"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")

    for doc, section in (
        (A1DOC, """

---

## 2026-10-19 周检补引（本地工作副本）

- 新增 **Sharma & Saxena 2026**（arXiv:2609.36101，readout 依赖）与 **Yaras et al. 2024**（arXiv:2412.07909，梯度流）两条引用，
  已在 `related_work.tex` 增一段区分（几何解释 vs 本稿的统计充分性 + margin 质量下界 + 证书）。
- 本地 main.tex 现 **59 页**（原 58），0/0/0；**投稿包保持 58 页冻结版**，`a1_paa` 审计的 I-02/I-06 为预期差异。
- 详见 `docs/REVISION_CITATION_BACKLOG_2026-10-19.md`。
"""),
        (PADOC, """

---

## 2026-10-19 周检补引（本地工作副本）

- `amblard2025fill` 由 arXiv 预印本升级为期刊版：*Int. J. Multimedia Information Retrieval* 15(4), 2026,
  DOI 10.1007/s13735-026-00423-w。
- 新增两条背景引用：Hu et al. 2026（arXiv:2609.37888，CLIP-CIL 视觉分支优于文本权重）与 He et al. 2026（arXiv:2609.36759，
  双模式低秩 + 原型桥）。均在 `sections/related_work.tex` gap 小节。
- 重编译：main_nc **70 页**、main_springer **50 页**，均 0/0/0；台账 76/76、96/96。**NC 投稿包未动。**
"""),
        (P3DOC, """

---

## 2026-10-19 周检补引（R1 之后的下一轮修回备料）

- 新增 **IFCLoRA**（arXiv:2607.22251，训练前零搜索分配）、**StatLoRA**（arXiv:2607.20205，假设检验 + 优化器 CLT）、
  **LoRA-GA²**（arXiv:2608.19800，多步梯度分配）三条引用与一段区分（IFCLoRA 最接近，但需校准集 + 图构造；
  本稿为闭式、无需搜索/校准/目标模型梯度）。
- 重编译 main.tex **10 页**、0/0/0；`audit_check.py` 0/0；`audit_pdf.py` 0/0。
- **R1 提交件未动**（编辑部明确在审期间不接受替换件），以上仅进 R2 备料。
"""),
    ):
        if not doc.exists():
            print(f"  skip missing {doc.name}")
            continue
        t = io.open(doc, encoding="utf-8").read()
        if "2026-10-19 周检补引" not in t:
            io.open(doc, "w", encoding="utf-8", newline="").write(t.rstrip("\n") + section)
            print(f"  appended: {doc.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
