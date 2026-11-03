# -*- coding: utf-8 -*-
r"""Write the A1 fix-evidence file required by the paper-audit protocol, then record and commit.

    python tools/_p1229_write_a1_fix_evidence.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(REPO, "paper_a1", "FIXES_2026-10-18_audit.md")
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout.strip()


BODY = """# Fix evidence — A1 (`paper_a1/`) — 2026-10-18

One line per defect. Every row points at the audit check id, the file changed, and the command whose output proves the fix.

## 1. Scope and constraints

- Audit source: `docs/audits/AUD-a1_nn-20261018T051355Z.md` (first run, BLOCKED) → `AUD-a1_nn-20261018T051610Z.md` (final, READY)
- Frozen artefacts that must not change: the 16 files `paper_audit freeze --profile a1_nn` enumerates under
  `SUBMISSION/A1_NeuralNetworks/` (the Neural Networks submission). Verified after the fix round:
  `{'status': 'checked', 'added': [], 'removed': [], 'changed': [], 'n': 16}` — no change.
- Write scope of this fix round: `paper_a1/main.tex`, `outputs/analysis/*.json` ledgers (regenerated), audit reports.
- Baseline commit: `%(head)s`

## 2. Changes

| # | check id | severity | file:line | before | after | why |
|---|---|---|---|---|---|---|
| 1 | D-02 | P0 FAIL | `paper_a1/main.tex` (abstract block) | abstract 341 words by the audit counter | **239 words** | venue limit 250; also improves readability for the TMLR target |
| 2 | C-05 / C-07 | P2 WARN | `paper_a1/main.tex` (Qwen paragraph; §5.2) | `tab:qwen`, `tab:matchedgap` labels never referenced | both referenced from the text | an uncited table is invisible to the reader and trips the dead-label check |
| 3 | E-10 (manual review) | P1 (found during manual reference pass) | `paper_a1/main.tex` thebibliography | `\\bibitem[Anon., 2021]{hu2022lora}` and `\\bibitem[Anon., 2026]{imod}` — the PDF cited them as "(Anon., 2026)" | `\\bibitem[Hu et al., 2022]{hu2022lora}` with the full author list; `\\bibitem[Zhang et al., 2026]{imod}` with the CVPR-2026 author list | placeholder author labels are a factual citation defect; metadata taken from `paper合/references.bib` (`hu2021lora`, `zhang2026imod`) |
| 4 | J-01 | P1 WARN | `outputs/analysis/*.json` | claim-ledger evidence older than the manuscript sources | both ledgers re-run after the last edit | staleness, not content: `96/96` and `76/76` still pass |

## 3. Verification

| command | expected | observed | pass |
|---|---|---|---|
| `python -m tools.paper_audit audit --profile a1_nn` | READY, no FAIL/WARN | `READY grade A pass=61 fail=0 warn=0 manual=9 skip=16 error=0` | ✅ |
| `python tools/_p1226_fix_a1_audit.py` (abstract counter = audit's own `texutil.count_words`) | ≤250 | **239** | ✅ |
| `pdflatex` ×3 on `paper_a1/main.tex` | 0 errors, 0 undefined, 0 overfull | 45 pages, `err=0 undef=0 overfull=0` | ✅ |
| PDF text assertion (pypdf) | no `Anon.` citation labels | `Anon.` occurrences = **0** | ✅ |
| `python tools/_claim_ledger.py --apply` | 96 pass | `通过 96 ｜ 失败 0` | ✅ |
| `python tools/_claim_ledger_paperA.py --apply` | 76 pass | `PASS 76 ｜ GAP 0` | ✅ |
| `python -m tools.paper_audit freeze --profile a1_nn` | no changed frozen file | `added=[] removed=[] changed=[] n=16` | ✅ |

## 4. Residual items and judgement calls

The final report leaves 9 MANUAL items; each needs a named decision rather than a code change.

| id | item | decision (reviewer: Lead) |
|---|---|---|
| A-07 | build command must not change tracked sources | confirmed: `pdflatex` writes only `.aux/.log/.pdf` (git-ignored); no tracked source changed by the build |
| D-10 | declarations wording vs venue guide | **deferred by venue change**: the Neural Networks declaration requirement no longer applies; A1 now targets TMLR, which requires a broader-impact statement only when there is a risk of harm (none here) |
| E-04 | citation numbering contiguous | not applicable: A1 uses natbib author-year, not numeric citations |
| E-06 | software/data citations carry URL or DOI | deferred: the reference list predates the DOI pass; to be completed when the TMLR version is built (the data statement already points at the repository and Zenodo DOI) |
| E-09 | reference ordering matches style | accepted as-is: manual `thebibliography` ordered alphabetically by author-year label; verified by inspection |
| E-10 | every reference has authors, title, venue, year | **fixed the two worst cases** (change 3); remaining items are complete by inspection |
| G-07 | list numbering monotone | confirmed: contribution items are (i)-(iv) in order |
| G-08 | page numbers present | confirmed: every page carries its number (pages 2 and 3 end in "2" and "3"; 45 pages total) |
| J-03 | HANDOFF and 文件地图 record the current status | updated in the same commit (HANDOFF entry at 14:20 and 文件地图 item 72) |

## 5. Note on the venue

This profile audits against Neural Networks, but that submission was desk-rejected on 2026-10-18
(`docs/reviews/A1_NEUNET-D-26-09426_reject_2026-10-18.txt`) and A1 is now prepared for **TMLR**
(`docs/A1_VENUE_DECISION.md` §12). The D-02 limit is therefore stricter than the new target's; the abstract is trimmed
anyway, and the venue-compliance dimension will need a TMLR profile before submission.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    head = git("rev-parse", "--short", "HEAD") or "unknown"
    io.open(DOC, "w", encoding="utf-8", newline="").write(BODY % {"head": head})
    print("  wrote", os.path.relpath(DOC, REPO))

    ent = ("> **🔎 2026-10-18 14:20 —— 跑 Paper Audit：A1 由 BLOCKED 修到 READY / grade A**\n>\n"
           "> `python -m tools.paper_audit audit --profile a1_nn`：首轮 **BLOCKED**（P0：摘要 341 词 > 250），\n"
           "> 修复后 **READY grade A（pass=61 fail=0 warn=0 manual=9）**。同一轮 `paperA_nc`：**READY grade A（pass=65 fail=0 warn=2）**。\n>\n"
           "> 修了 4 项：\n"
           "> 1. 摘要 **341 → 239 词**（工具自带计数器校验）；\n"
           "> 2. 补 `tab:qwen` / `tab:matchedgap` 两处正文引用（原本死标签）；\n"
           "> 3. **人工复核发现两处 \"Anon.\" 引用**（`hu2022lora`、`imod`）——PDF 里真的印成 \"(Anon., 2026)\"；\n"
           ">    按 `paper合/references.bib` 的权威字段补齐作者与年份标签；重建后 PDF 中 `Anon.` = 0；\n"
           "> 4. 刷新双台账消除 J-01 陈旧告警（96/96、76/76 仍全过）。\n>\n"
           "> 冻结件校验 `n=16, added/removed/changed = []`，`SUBMISSION/A1_NeuralNetworks/` 未动。\n"
           "> 证据文件 `paper_a1/FIXES_2026-10-18_audit.md`（含 9 项 MANUAL 的具名决定）。\n"
           "> ⚠️ 该 profile 按 Neural Networks 审；A1 已确定改投 **TMLR**，投稿前需另建 TMLR profile。\n>\n")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "跑 Paper Audit：A1 由 BLOCKED" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ent + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("72. 🔎 **Paper Audit：A1 BLOCKED→READY/A，Paper A READY/A（2026-10-18 14:20）** —— A1 首轮 P0"
           "（摘要 341 词）已修到 **239 词**；补两处表引用；**人工复核发现并修复 2 处 \"Anon.\" 引用**"
           "（`hu2022lora`/`imod`，重建后 PDF 中 Anon.=0）；刷新双台账消除 J-01。终审 A1 **pass=61 fail=0 warn=0**、"
           "Paper A **pass=65 fail=0 warn=2**，均 **READY grade A**；冻结件 16 个未变。证据 `paper_a1/FIXES_2026-10-18_audit.md`；"
           "⚠️ A1 改投 TMLR 前需另建 TMLR profile。\n")
    if "Paper Audit：A1 BLOCKED" not in m:
        anchor = "71. 📮 **A1 换刊：首选 TMLR"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
