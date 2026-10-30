# -*- coding: utf-8 -*-
r"""Record the independent-audit fix round.

    python tools/_p1474_record_audit_fixes.py --apply
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
EVID = os.path.join(REPO, "docs", "EVIDENCE_MAP_2026-10-19.md")

ENTRY = """> **🔎 2026-10-21 09:10 —— 独立子智能体审计 + 全部问题修复（2 P1 + 5 P2）**
>
> 审计方：独立只读子智能体（未改文件），发现并已修复：
>
> | 编号 | 问题 | 修复 |
> |---|---|---|
> | **P1-1** | P3 补充材料在 IEEEtran 双栏中用 `longtable` → 报错、S13–S15 丢失、包内仍是旧 6 页 PDF | S13 改为 `table*`；在 `supplementary/` 目录内编译（bib 命中）；**补一 7 页、0 错、0 overfull、0 未定义、0 `[?]`**；包内 `Supplementary.pdf`（7 页）与 README 已更新；`audit_pdf.py` 页数 6→7、节数 S1–S15 |
> | **P1-2** | A1 包内 cover letter 是 **Neural Networks** 旧信 | 改用 `paper_a1/cover_letter_paa_revision.pdf`（PAA）；源 zip 排除所有 cover letter；打包器新增 `--zip-exclude` 与包目录**先清空后重建**，防止陈旧文件残留 |
> | **P2-1** | A23 评测集表列名 32/64/128/256 与实际 n_eval 67/67/67/201 不符 | 重跑分层抽样 **67/134/268/536/1608**；正文与表更新（BioCLIP 0.48/0.52/0.86/0.91/0.83；OceanCLIP −0.64/0.49/0.27/0.27/0.61；"<约 270 张不可靠"）|
> | **P2-2** | Paper A β CV 写 1.27–1.77，实为 1.27–1.76 | 已改 1.76 |
> | **P2-3** | P3 补充 `tab:seed5`/`tab:numsamples` 为死标签 | S14/S15 正文各加 `Table~\ref{...}` |
> | **P2-4** | 修回 cover letter 页数过期（A1 61→64；PaperA 72→74；P3 补 6→7）| 已改并重编译 |
> | **P2-5** | 三个 provenance 附录未列新增 float | 由 manifest 重新生成，新增 `tab:monitor_variants` / `tab:watertank96`+`tab:neval` / `tab:odefit` 行 |
>
> 外部副作用修复：打包器支持 `--supplementary`（P3 包 README 列出 7 页补充），包目录清理后重建 → staged **1:1**（64/69/10/74/7）。
> 终态审计：A1/PaperA-NC 仅预期 I-02（+I-06），其余四门 **READY 0 warn**；P3 `audit_pdf` 0/0、`audit_check` 0/0；A23 verify PASS；Commentary final check PASS；provenance gate PASS。
>

"""

ROW = ("129. 🔎 **独立审计 + 问题修复（2026-10-21 09:10）** —— 子智能体发现 2 P1 + 5 P2：P3 补材 longtable→table*"
       "（7 页、0/0/0/0、包已换新）；A1 包错装 Neural Networks 封面信→改 PAA revision 并清空重建；A23 评测集重跑"
       "67/134/268/536/1608；β CV 1.76；P3 死标签；修回信页数 64/74/7；provenance 附录补三行。staged 1:1（64/69/10/74/7）。\n")

EVID_ROWS = """| `a23_neval_sensitivity.json`（v2） | A23 评测集分层重跑（67/134/268/536/1608） | `tools/_p1415_a23_neval.py` |
| 包修复脚本 | `--zip-exclude` / `--supplementary` / 清空重建 | `tools/_p1336_build_venue_package.py`, `tools/_p1445_rebuild_packages.py` |
| P3 补材修复 | longtable→table* + S14/S15 引用 | `tools/_p1470_p3_supp_fix.py` |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "独立子智能体审计 + 全部问题修复" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "独立审计 + 问题修复（2026-10-21 09:10）" not in m:
        anchor = "128. 📝 **全部复核并写进论文"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + ROW + m[end + 1:])
        print("  file map updated")
    e = io.open(EVID, encoding="utf-8").read()
    if "P3 补材修复" not in e:
        io.open(EVID, "w", encoding="utf-8", newline="").write(e.rstrip() + "\n" + EVID_ROWS)
        print("  evidence map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
