# -*- coding: utf-8 -*-
r"""整理投稿包（二）：Paper A、P3、综述、A23_JOE 补齐 + `SUBMISSION/README.md` 总索引（2026-10-12）。

| 稿 | 来源 | 目标目录 |
|---|---|---|
| **Paper A** | `paper合/NC_submission/`（10-12 16:03） | `SUBMISSION/PaperA_Neurocomputing/` |
| **P3** | `paper3/paper_ieee/PRL_submission/`（09-29） | `SUBMISSION/P3_PRL/` |
| **综述** | `paper_review_prl/`（10-06） | `SUBMISSION/Review_PRL/` |
| **A23** | `paper_a2/`（10-06） | `SUBMISSION/A23_JOE/`（补齐当前件） |

    python tools\_p351_organize_submission2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUB = REPO / "SUBMISSION"


def copy_tree(src: Path, dst: Path, patterns, log: list, label: str, exclude_dirs=()):
    if not src.exists():
        log.append(f"  ⚠️ {label}: 源缺失 {src.relative_to(REPO)}")
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        if any(skip in p.parts for skip in exclude_dirs):
            continue
        if patterns and not any(p.match(g) for g in patterns):
            continue
        rel = p.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
        n += 1
    log.append(f"  ✅ {label}: 复制 {n} 个文件 → {dst.relative_to(REPO)}")
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    log = []

    # ---- Paper A ----
    pa = SUB / "PaperA_Neurocomputing"
    copy_tree(REPO / "paper合" / "NC_submission", pa,
              ["*.pdf", "*.txt", "*.md", "*.zip"], log, "Paper A",
              exclude_dirs=("latex_source",))
    # latex_source 也带上（源码包，供编辑部要求时用）
    copy_tree(REPO / "paper合" / "NC_submission" / "latex_source", pa / "latex_source",
              None, log, "Paper A latex_source")
    (pa / "README.md").write_text(f"""# Paper A（P1+P2 合并）→ Neurocomputing

| 项 | 内容 |
|---|---|
| 稿件 | `paper合/`（源码目录） |
| 目标刊 | **Neurocomputing**（ISSN 0925-2312） |
| 模板 | Elsevier `elsarticle`（`main_nc.tex`）；另有 Springer 版 `main_springer.tex` |
| 页数 / 编译 | NC **60 页**、Springer **44 页**，**0 错误 / 0 未定义 / 0 Overfull** |
| 摘要 | **250 词**（Neurocomputing 限 250） |
| **投稿状态** | 🔴 **从未向任何期刊投稿** |
| 前史 | 本稿的实证部分源于 P1（`paper/`），P1 投 **Pattern Recognition**（`PR-D-26-10149`）**已被拒** |
| PR 意见 | ✅ Pattern Recognition 审稿意见**全部改入**，`tools/_p290_final_pr_audit.py` **26/26 通过** |
| 整理时间 | {time.strftime('%Y-%m-%d %H:%M')} |

## 文件清单

| 文件 | 用途 |
|---|---|
| `Manuscript.pdf` | **主稿（60 页）** |
| `Cover Letter.pdf` | 投稿信 |
| `Highlights.pdf` / `Highlights.txt` | Highlights（PDF + 纯文本，系统常要文本） |
| `latex_source.zip` | LaTeX 源码包 |
| `latex_source/` | 同一源码的**解包副本**（便于核对） |
| `README.md` | 本文件 |

## 如何重编译

```powershell
cd paper合
pdflatex -interaction=nonstopmode main_nc.tex
bibtex main_nc
pdflatex -interaction=nonstopmode main_nc.tex
pdflatex -interaction=nonstopmode main_nc.tex
```

## ⚠️ 投稿前需处理

1. **与 A1 的关系须在 cover letter 披露**（A1 目标同为 Elsevier；两稿都做 PEFT 下 modality gap）。
2. **同出版商披露**：PRL 还有两稿在审（`PRLETTERS-D-26-02378` P3、`PRLETTERS-D-26-02402` 综述）。
3. 目标刊由操作者最终确认（NC 就绪；备选见 `docs/PAPERA_VENUE_OPTIONS.md`）。
""", encoding="utf-8")
    log.append("  ✅ Paper A README 已写")

    # ---- P3 ----
    copy_tree(REPO / "paper3" / "paper_ieee" / "PRL_submission", SUB / "P3_PRL",
              None, log, "P3")
    (SUB / "P3_PRL" / "README.md").write_text(f"""# P3 → Pattern Recognition Letters

| 项 | 内容 |
|---|---|
| 稿件 | `paper3/paper_ieee/` |
| 稿号 | **`PRLETTERS-D-26-02378`** |
| 状态 | 🔄 **在审**（提交 2026-09-26 16:22） |
| 前史 | TNNLS `TNNLS-2026-P-50569` → **2026-09-03 被拒**（明确"不要修改版"） |
| 整理时间 | {time.strftime('%Y-%m-%d %H:%M')} |

## 注意

- 本稿**在审中** → **不得**再投他处。
- 与 `paper_ap3`（P1+P2+P3 合并稿）**内容重叠**：ap3 **因含本稿内容而不可投**。
""", encoding="utf-8")
    log.append("  ✅ P3 README 已写")

    # ---- 综述 ----
    copy_tree(REPO / "paper_review_prl", SUB / "Review_PRL", None, log, "综述 Commentary")
    (SUB / "Review_PRL" / "README.md").write_text(f"""# 综述/Commentary → Pattern Recognition Letters

| 项 | 内容 |
|---|---|
| 稿件 | `paper_review_prl/` |
| 稿号 | **`PRLETTERS-D-26-02402`** |
| 类型 | **Commentary** |
| 标题 | *Allocation, not selection: comparability in parameter-efficient multimodal adaptation* |
| 状态 | 🔄 **在审**（本项目首次"同刊两篇在审"：`-02378` + `-02402`） |
| 篇幅 | **7 页**（上限 7） |
| 整理时间 | {time.strftime('%Y-%m-%d %H:%M')} |

## 注意

- 与 `PRLETTERS-D-26-02378`（P3）**互不引用、无共享整句**（实测 0 条），cover letter 已主动披露同刊另一篇在审。
""", encoding="utf-8")
    log.append("  ✅ 综述 README 已写")

    # ---- A23 补齐 ----
    copy_tree(REPO / "paper_a2", SUB / "A23_JOE" / "current",
              ["*.tex", "*.pdf", "*.docx", "*.zip", "*.bib"], log, "A23 当前件")
    for l in log:
        print(l)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
