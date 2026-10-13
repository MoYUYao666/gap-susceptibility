# -*- coding: utf-8 -*-
r"""建立 P3（PRL）修订包目录并备份回信相关材料（2026-10-13）。

## 为什么需要

PRL `PRLETTERS-D-26-02378` 收到 **Revise**（截止 **2026-11-02**），要求
**在 EM 平台逐条 reply to reviews**。当前：
- `SUBMISSION/P3_PRL/` = **投稿时**的包（2026-09-26）
- **修订阶段的材料散落**在 `docs/`、`outputs/analysis/`、`tool s/`
- **修订包目录尚未建立**

⇒ 本脚本建 `SUBMISSION/P3_PRL_revision/`，把回信与依据**集中备份**（复制，不改原件）。

## 结构

```
SUBMISSION/P3_PRL_revision/
  README.md                    修订包索引（含状态、截止、逐项去哪找）
  reviews/                     审稿意见原文（编辑邮件 + 审稿 PDF + 提取文本）
  response/
    P3_REVIEW_RESPONSE.md      33 条逐条应答（工作文档）
    P3_REVIEW_RESPONSE.txt     纯文本副本（便于贴进 EM 表单）
  evidence/                    三组补实验的报告 + 解析后的意见与分类
  manuscript/                  当前稿件 PDF（14 页，**非投稿版**，标注清楚）
```

    python tools\_p461_backup_prl_response.py [--apply]
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
DEST = REPO / "SUBMISSION" / "P3_PRL_revision"

COPY = {
    # 审稿意见原文
    "reviews/PRL Revison.txt": "docs/_inbox/P3_reviews/PRL Revison.txt",
    "reviews/PRLETTERS-D-26-02378-reviews.pdf": "docs/_inbox/P3_reviews/PRLETTERS-D-26-02378-reviews.pdf",
    "reviews/_reviews_extracted.txt": "docs/_inbox/P3_reviews/_reviews.txt",
    # 回信
    "response/P3_REVIEW_RESPONSE.md": "docs/P3_REVIEW_RESPONSE.md",
    # 依据
    "evidence/P3_EXPERIMENTS.md": "docs/P3_EXPERIMENTS.md",
    "evidence/P3_DOWNSTREAM.md": "docs/P3_DOWNSTREAM.md",
    "evidence/P3_STATS.md": "docs/P3_STATS.md",
    "evidence/p3_reviews_parsed.json": "outputs/analysis/p3_reviews_parsed.json",
    "evidence/p3_review_classes.json": "outputs/analysis/p3_review_classes.json",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print(f"  （预演）将建 {DEST.relative_to(REPO)} 并复制 {len(COPY)} 个文件")
        return 0

    for sub in ("reviews", "response", "evidence", "manuscript"):
        (DEST / sub).mkdir(parents=True, exist_ok=True)

    n = 0
    print("=== 复制 ===")
    for dst, src in COPY.items():
        sp = REPO / src
        dp = DEST / dst
        if not sp.exists():
            print(f"  ⚠️ 缺原文件 {src}")
            continue
        shutil.copy2(sp, dp)
        n += 1
        print(f"  ✅ {dst:<46} ← {src}")

    # 稿件 PDF（标注为"修订中"版本）
    ms = REPO / "paper3" / "paper_ieee" / "main.pdf"
    if ms.exists():
        shutil.copy2(ms, DEST / "manuscript" / "main_REVISING.pdf")
        n += 1
        pg = ""
        try:
            r = subprocess.run(["pdfinfo", str(ms)], capture_output=True,
                               encoding="utf-8", errors="replace")
            for ln in (r.stdout or "").splitlines():
                if ln.startswith("Pages:"):
                    pg = ln.split(":", 1)[1].strip()
        except Exception:
            pass
        print(f"  ✅ manuscript/main_REVISING.pdf（{pg} 页）← paper3/paper_ieee/main.pdf")

    # 纯文本副本（便于贴进 EM 表单）
    resp = REPO / "docs" / "P3_REVIEW_RESPONSE.md"
    if resp.exists():
        t = io.open(resp, encoding="utf-8", errors="replace").read()
        io.open(DEST / "response" / "P3_REVIEW_RESPONSE.txt", "w",
                encoding="utf-8", newline="").write(t)
        n += 1
        print(f"  ✅ response/P3_REVIEW_RESPONSE.txt（{len(t)} 字符）")

    # README
    readme = f"""# P3 修订包（PRL `PRLETTERS-D-26-02378`）

> **状态**：收到 **Revise**（可修改后重审）｜**截止 2026-11-02**（逾期视为撤稿）
> **编辑**：Yonghuai Liu（Editor-in-Chief），Pattern Recognition Letters
> **平台要求**：**必须在 Editorial Manager 逐条 reply to reviews**
> **备份时间**：{time.strftime('%Y-%m-%d %H:%M')}

## 目录

| 路径 | 内容 |
|---|---|
| `reviews/` | **审稿意见原文**：编辑决定邮件（`.txt`）+ 审稿意见 PDF + 提取文本（33 条） |
| `response/` | **逐条应答**：`P3_REVIEW_RESPONSE.md`（工作文档，含建议动作 + 空回复块）与 `.txt` 副本 |
| `evidence/` | **补实验依据**：三组报告（E/F+G/I）与意见解析/分类 JSON |
| `manuscript/` | **当前稿件 PDF（修订中，14 页）** —— ⚠️ **不是投稿版**（投稿版 11 页见 `../P3_PRL/`） |

## 意见量与分组

**33 条**（R1 5 ｜ R2 5 ｜ R3 23），编号全部连续；集中于 **10 个根问题**（见 `response/` 内文档开头表格）。

## 三组补实验（依据在 `evidence/`）

| 组 | 覆盖意见 | 报告 | 关键结果 |
|---|---|---|---|
| **E** | R2.2 / R2.4 / R3.9 / R3.21 | `P3_EXPERIMENTS.md` | 真逐块 Γ 引导分配（**参数量逐位相同 = 7,237,632**）；Γ-guided **优于 uniform（p=0.024，未过 Bonferroni）**、**未胜随机**、**反序同样** |
| **F+G** | R1.3 / R1.4 / R2.3 / R3.13–R3.16 / R3.23 | `P3_DOWNSTREAM.md` | 真实图文复跑；**下游检验与能量相反**；**blank 非中性**；**论文操作点上 blank 的 $E_0$ 是 real 的 3.09×** |
| **I** | R3.4 / R3.17–R3.22 | `P3_STATS.md` | **"30×" 必须删**（$\\eta^2=0.989$）；**"sharp transition" 降级**；**NaN=表示塌缩可加强**；**功效不足**（所需 $n\\approx87$） |

## 已改入稿件的关键项（Lead 落笔，共 23 处）

理论缺口（新增 R3′ + Lemma + 反例）｜记账口径（rank vs 参数，2.65×）｜β 来源更正｜容量混淆｜30× 降级｜零样本绝对否定收窄｜**"optimal" 限定为 alignment energy**｜**论文操作点 3.09× 的 blank 探针测量**

## ⚠️ 待办（未完成，不得当作已交付）

1. **P1（随机池 30 run）尚未跑满** → "未胜随机"那段仍标 **provisional**，待定稿
2. **页数**：当前 **14 页**（投稿 11 页）→ 需压缩 + 可能新建 Supplementary
3. **33 条回复的正式文本尚未撰写**（工作文档已就绪，待数字定稿）
4. `theory.tex` 两处 **(A3) 同名不同义** → 需改编号
5. 论文侧**有效 n 口径**（4 个评估样本是否等价）→ 回复信需澄清

## 纪律

- **每个数字都能指名产出脚本与归档文件+字段**；无来源的数字一律删除
- **修订提交时必须上传源文件**（编辑部明确：只交 PDF 会延误）
- **备份 ≠ 定稿**：本目录是**当前状态快照**，修订提交前须重新生成
"""
    io.open(DEST / "README.md", "w", encoding="utf-8", newline="").write(readme)
    n += 1
    print(f"  ✅ README.md")

    print(f"\n  → 共 {n} 个文件写入 {DEST.relative_to(REPO)}")
    print("\n=== 复核 ===")
    for sub in ("", "reviews", "response", "evidence", "manuscript"):
        p = DEST / sub if sub else DEST
        items = sorted(p.iterdir()) if p.is_dir() else []
        print(f"  {(sub or '(根)'):<14} {len(items)} 项")
        for it in items:
            tag = f"{it.stat().st_size:,} B" if it.is_file() else "[目录]"
            print(f"       {it.name:<46} {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
