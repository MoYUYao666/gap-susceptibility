# -*- coding: utf-8 -*-
r"""重新生成 P3 修订包（含 10 页投稿件 + 补充材料 + 正式回复信）（2026-10-13）。

## 依据

- **操作者选定篇幅档 ①：10 页**（含全部 33 条意见所需证据）
- **PRL Guide 硬约束**：双栏 ≤7 页（Mandatory Submission Requirements 第 1 条）⇒ **需在 cover letter 主动说明**
- **33 条回复信已完成**：`docs/P3_RESPONSE_LETTER.md`（41,457 字符，覆盖 33/33）

## 产出

```
SUBMISSION/P3_PRL_revision/
  README.md                    修订包索引（状态/截止/逐项去处/待办）
  response/P3_RESPONSE_LETTER.md + .txt    33 条正式回复
  response/P3_REVIEW_RESPONSE.md           工作文档（含建议动作）
  manuscript/main.pdf                      10 页投稿件
  manuscript/supplementary.pdf             补充材料
  manuscript/latex_source/                 tex 源（main + sections + supplementary）
  reviews/                                 审稿意见原文
  evidence/                                三组补实验报告 + 解析 JSON
```

    python tools\_p532_regen_revision_package.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
DEST = REPO / "SUBMISSION" / "P3_PRL_revision"

COPY = [
    ("reviews/PRL Revison.txt", "docs/_inbox/P3_reviews/PRL Revison.txt"),
    ("reviews/PRLETTERS-D-26-02378-reviews.pdf", "docs/_inbox/P3_reviews/PRLETTERS-D-26-02378-reviews.pdf"),
    ("reviews/_reviews_extracted.txt", "docs/_inbox/P3_reviews/_reviews.txt"),
    ("response/P3_RESPONSE_LETTER.md", "docs/P3_RESPONSE_LETTER.md"),
    ("response/P3_REVIEW_RESPONSE.md", "docs/P3_REVIEW_RESPONSE.md"),
    ("evidence/P3_EXPERIMENTS.md", "docs/P3_EXPERIMENTS.md"),
    ("evidence/P3_DOWNSTREAM.md", "docs/P3_DOWNSTREAM.md"),
    ("evidence/P3_STATS.md", "docs/P3_STATS.md"),
    ("evidence/P3_COMPRESSION.md", "docs/P3_COMPRESSION.md"),
    ("evidence/p3_reviews_parsed.json", "outputs/analysis/p3_reviews_parsed.json"),
    ("evidence/p3_reviews_structured.json", "outputs/analysis/p3_reviews_structured.json"),
    ("evidence/p3_page_feasibility.json", "outputs/analysis/p3_page_feasibility.json"),
    ("evidence/p3_compress_allocation.json", "outputs/analysis/p3_compress_allocation.json"),
]
LATEX = ["main.tex", "main_body_full.tex", "main_full.tex",
         "sections/introduction.tex", "sections/related_work.tex", "sections/theory.tex",
         "sections/experiments.tex", "sections/discussion.tex", "sections/conclusion.tex",
         "sections/appendix.tex", "supplementary/supplementary.tex", "references.bib"]


def pdfpages(p: Path):
    if not p.exists():
        return "?"
    r = subprocess.run(["pdfinfo", str(p)], capture_output=True, encoding="utf-8", errors="replace")
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("Pages:"):
            return ln.split(":", 1)[1].strip()
    return "?"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for sub in ("reviews", "response", "evidence", "manuscript", "manuscript/latex_source"):
        (DEST / sub).mkdir(parents=True, exist_ok=True)

    n = 0
    print("=== 复制 ===")
    for dst, src in COPY:
        sp, dp = REPO / src, DEST / dst
        if not sp.exists():
            print(f"  ⚠️ 缺 {src}")
            continue
        shutil.copy2(sp, dp)
        n += 1
        print(f"  ✅ {dst:<44} ← {src}")

    print()
    print("=== 稿件 ===")
    mp = PI / "main.pdf"
    if mp.exists():
        shutil.copy2(mp, DEST / "manuscript" / "main.pdf")
        n += 1
        print(f"  ✅ manuscript/main.pdf（{pdfpages(mp)} 页 = 投稿件）")
    sp = PI / "supplementary" / "supplementary.pdf"
    if sp.exists():
        shutil.copy2(sp, DEST / "manuscript" / "supplementary.pdf")
        n += 1
        print(f"  ✅ manuscript/supplementary.pdf（{pdfpages(sp)} 页）")
    fp = PI / "main_full.pdf"
    if fp.exists():
        shutil.copy2(fp, DEST / "manuscript" / "main_full.pdf")
        n += 1
        print(f"  ✅ manuscript/main_full.pdf（{pdfpages(fp)} 页 = 完整版存档）")

    print()
    print("=== LaTeX 源 ===")
    for f in LATEX:
        srcp = PI / f
        if not srcp.exists():
            print(f"  ⚠️ 缺 {f}")
            continue
        dstp = DEST / "manuscript" / "latex_source" / f
        dstp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(srcp, dstp)
        n += 1
    print(f"  ✅ 复制 {len(LATEX)} 个源文件")

    # 回复信纯文本（便于贴 EM 表单）
    rl = REPO / "docs" / "P3_RESPONSE_LETTER.md"
    if rl.exists():
        io.open(DEST / "response" / "P3_RESPONSE_LETTER.txt", "w",
                encoding="utf-8", newline="").write(
            io.open(rl, encoding="utf-8", errors="replace").read())
        n += 1
        print("  ✅ response/P3_RESPONSE_LETTER.txt（EM 表单用）")

    readme = f"""# P3 修订包（PRL `PRLETTERS-D-26-02378`）

> **状态**：**Revise**（可修改后重审）｜**截止 2026-11-02**（逾期视为撤稿）
> **编辑**：Yonghuai Liu（Editor-in-Chief）｜**平台要求**：必须在 EM **逐条 reply to reviews**
> **生成时间**：{time.strftime('%Y-%m-%d %H:%M')}
> **投稿件页数**：**{pdfpages(mp)} 页**（操作者选定档 ①；完整版 {pdfpages(fp)} 页另存）

## 目录

| 路径 | 内容 |
|---|---|
| `reviews/` | 审稿意见原文（编辑邮件 + 审稿 PDF + 提取文本，33 条） |
| `response/P3_RESPONSE_LETTER.md` | **33 条正式逐条回复**（可直接贴 EM 表单；`.txt` 为纯文本版） |
| `response/P3_REVIEW_RESPONSE.md` | 应答工作文档（含每条的建议动作与根问题归纳） |
| `manuscript/main.pdf` | **投稿件（{pdfpages(mp)} 页）** |
| `manuscript/supplementary.pdf` | 补充材料（公理推导/证明/协议细节/逐 run 表/表图） |
| `manuscript/main_full.pdf` | 完整版存档（{pdfpages(fp)} 页，**非投稿件**） |
| `manuscript/latex_source/` | LaTeX 源（编辑部要求**必须上传源文件**，只交 PDF 会延误） |
| `evidence/` | 三组补实验报告 + 意见解析/结构化 JSON + 篇幅可行性量化 |

## 本次修订的 11 项变更（详见回复信开头的汇总表）

**理论更正** R3′ 公理 + 反例（R1.5/R3.1/R3.3）｜**新实验** 真逐块 Γ 引导分配、同预算逐位对齐（R2.2/R3.9/R3.21）｜
**新实验** 下游检验（R1.3/R2.3/R3.15/R3.16）｜**新测量** blank 探针 3.09×（R1.4/R3.13/R3.14/R3.23）｜
**新数据** 逐块 Γ + rank 表（R3.12）｜**新分析** 跨环境可复现性（R3.18）

### ⚠️ 四项主张**已撤回/降级**（写在稿件与回复信里）

1. **"Γ-guided 优于 uniform"** —— 另一学习率下反转、匹配训练损失后消失（**撤回**）
2. **"phase transition 尖锐"** —— 改为 **bracketed**，且位置属测量协议（**降级**）
3. **"architecture-dependent"** —— 差异随视觉 token 预算，非架构（**撤回**）
4. **"30× 方差比"** —— $\eta^2=0.989$，是秩间方差（**撤回**）

**另有如实报告的不利结果**：**AdaLoRA 在对称调 lr 后 ΔE 优于我们全部方案**（−1468/−757 vs +1478）。

## ⚠️ 提交前必办

1. **cover letter 必须主动说明篇幅与 Guide 的关系**（Guide 第 1 条要求双栏 ≤7 页；本稿 10 页，
   原投稿 11 页且进了外审）**并请编辑裁定** —— 回复信开头已写明
2. **上传 LaTeX 源文件**（`manuscript/latex_source/`）
3. **Authorship Confirmation 表单**必须在 EM 的 `Attach Files` 以 item type **Cover Letter** 上传
   （Guide 第 4 条：**未照办会 AUTOMATIC REJECTION**）
4. **逐条回复在 EM 的表单里填写**（不能只交 PDF）

## 复现

- 逐条回复覆盖核验：`python tools/_p530_verify_response_letter.py`
- 矛盾扫描（要求"需处理 0 处"）：`python tools/_p497_scan_contradictions.py`
- 断头命令检查（要求 0 处）：`python tools/_p515_fix_severed_final.py`
- 字面 `\\n` 检查（要求 0）：`python tools/_p503_fix_literal_n_correct.py`
- 篇幅可行性量化：`python tools/_p524_page_feasibility.py`
"""
    io.open(DEST / "README.md", "w", encoding="utf-8", newline="").write(readme)
    n += 1
    print("  ✅ README.md")
    print()
    print(f"  → 共 {n} 个文件写入 {DEST.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
