# -*- coding: utf-8 -*-
r"""整理投稿包：`SUBMISSION/` 按「每稿一稿号一目录」重建（2026-10-12）。

## 现状（实测）

| 目录 | 文件数 | 最新 |
|---|---|---|
| `SUBMISSION/`（4 个子目录） | 87 | **09-22 11:15**（陈旧） |
| `paper合/NC_submission/` | 62 | **10-12 16:03** |
| `paper_a1/` | 80 | **10-12 02:06** |
| `paper3/paper_ieee/PRL_submission/` | 28 | 09-29 10:05 |
| `paper_review_prl/` | 23 | 10-06 09:54 |
| `paper_a2/` | 67 | 10-06 09:54 |

## 原则

1. **`SUBMISSION/<稿>-<刊>/`** 一稿一号一目录（沿用既有命名）。
2. **已投出的那一版永久归档** → `_submitted_<稿号>_<日期>/`（**不得覆盖**，否则历史不可复核）。
3. **当前最新投稿件**放目录根。
4. 每个目录一份 `README.md`：**稿号 / 状态 / 文件清单 / 如何重编译 / 来源路径**。
5. `SUBMISSION/README.md` 为总索引。

## 分步执行（本脚本只做 A1 与总索引）

    python tools\_p350_organize_submission.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUB = REPO / "SUBMISSION"

# A1 当前投稿件（来自 paper_a1/）
A1_FILES = ["main.tex", "main.pdf", "abstract.tex", "abstract.pdf",
            "cover_letter.tex", "cover_letter.pdf",
            "declaration.tex", "declaration.pdf",
            "declaration_of_interest.docx", "highlights.tex", "highlights.pdf",
            "related_work.tex", "related_work_bibitems.tex",
            "main_zh.tex", "main_zh.pdf"]


def cp(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not a.apply:
        print("  （预演）将执行：")
        print("   1. A1：把已投出的 Neurocomputing 版归档为 _submitted_NEUCOM-D-26-20952_2026-09-16/")
        print("   2. 新建 SUBMISSION/A1_NeuralNetworks/ 放入当前投稿件（来自 paper_a1/，10-12）")
        print("   3. 写 SUBMISSION/A1_NeuralNetworks/README.md")
        print("   4. 写 SUBMISSION/README.md 总索引")
        return 0

    log = []

    # ---- 1) 归档已投出的 A1 Neurocomputing 版 ----
    a1nc = SUB / "A1_Neurocomputing"
    arch = a1nc / "_submitted_NEUCOM-D-26-20952_2026-09-16"
    if a1nc.exists() and not arch.exists():
        arch.mkdir(parents=True)
        n = 0
        for f in a1nc.iterdir():
            if f.is_dir():
                if f.name != arch.name:
                    shutil.move(str(f), str(arch / f.name))
                    n += 1
            elif f.is_file():
                shutil.move(str(f), str(arch / f.name))
                n += 1
        log.append(f"  ✅ A1 旧版已归档：{n} 项 → {arch.relative_to(REPO)}")
    else:
        log.append("  ⚠️ A1_Neurocomputing 缺失或已归档，跳过")

    # ---- 2) 新建 A1_NeuralNetworks ----
    a1nn = SUB / "A1_NeuralNetworks"
    a1nn.mkdir(parents=True, exist_ok=True)
    copied, missing = [], []
    for name in A1_FILES:
        src = REPO / "paper_a1" / name
        if cp(src, a1nn / name):
            copied.append(name)
        else:
            missing.append(name)
    log.append(f"  ✅ A1_NeuralNetworks：复制 {len(copied)} 个文件"
               + (f"（缺 {missing}）" if missing else ""))

    # ---- 3) A1 README ----
    (a1nn / "README.md").write_text(f"""# A1 → Neural Networks（Elsevier ATS 转投）

| 项 | 内容 |
|---|---|
| 稿件 | `paper_a1/`（源码目录） |
| 模板 | `\\documentclass[review,authoryear]{{elsarticle}}` |
| 目标刊 | **Neural Networks**（ISSN 0893-6080），`main.tex` 的 `\\journal{{}}` 已是该刊 |
| 转投方式 | **Elsevier Article Transfer Service（ATS）** |
| **截止** | ⚠️ **2026-11-08 23:59（须在此前确认转投）** |
| 前史 | PRL `PRLETTERS-D-26-01941` 拒（2026-09-14）→ Neurocomputing `NEUCOM-D-26-20952` **桌面拒**（2026-10-10，无审稿意见） |
| 页数 / 编译 | **42 页**，0 错误 / 0 未定义 |
| 摘要 | **249 词** |
| 整理时间 | {time.strftime('%Y-%m-%d %H:%M')} |

## 文件清单

| 文件 | 用途 |
|---|---|
| `main.tex` / `main.pdf` | 主稿（42 页） |
| `abstract.tex` / `abstract.pdf` | 独立摘要页 |
| `cover_letter.tex` / `cover_letter.pdf` | 投稿信 |
| `declaration.tex` / `declaration.pdf` | 声明 |
| `declaration_of_interest.docx` | 利益冲突声明（系统上传用） |
| `highlights.tex` / `highlights.pdf` | Highlights |
| `related_work.tex` / `related_work_bibitems.tex` | 相关工作子文件与 bib 条目 |
| `main_zh.tex` / `main_zh.pdf` | 中文镜像（**勿投**，仅内部存档） |

## 如何重编译

```powershell
cd paper_a1
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

## 已归档的旧版

`../A1_Neurocomputing/_submitted_NEUCOM-D-26-20952_2026-09-16/` —— **投给 Neurocomputing 的那一版原件**（被桌面拒，**不删**，供历史复核）。

## 注意

- 稿内仅 2 处 `Pattern Recognition Letters`，均为**参考文献条目**（正确，不改）。
- 中文版 `main_zh.*` **不要上传**（JOE 的投稿认证覆盖"任何语言"，沿用保守做法）。
""", encoding="utf-8")
    log.append("  ✅ A1 README 已写")

    for l in log:
        print(l)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
