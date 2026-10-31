# -*- coding: utf-8 -*-
r"""补齐 `SUBMISSION/` 里两个缺 README 的历史目录（2026-10-12）。

`_p352` 核验发现 `A1_Neurocomputing/` 与 `A23_JOE/` 根目录无 README
（前者因归档移动、后者原本只在 `supplementary/` 里有 `README.txt`）。

    python tools\_p354_submission_readmes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUB = REPO / "SUBMISSION"

TEXTS = {
    "A1_Neurocomputing": """# A1 → Neurocomputing（**历史存档，已失效**）

| 项 | 内容 |
|---|---|
| 稿件 | `paper_a1/`（现源码目录） |
| 稿号 | **`NEUCOM-D-26-20952`** |
| 提交 | 2026-09-16 04:58 |
| 决定 | 🔴 **桌面拒稿（2026-10-10）** |
| 理由 | *"falls within the aim and scope of our journal, it did not meet the significance level required"* |
| 审稿意见 | **无**（`Comments to Authors:` 与 `Editor's comments` 均空） |
| 转投 | 有（Elsevier ATS）→ **目标 Neural Networks**，须 **2026-11-08 23:59** 前确认 |
| 前史 | PRL `PRLETTERS-D-26-01941` 拒（2026-09-14） |

## ⚠️ 本目录的用法

- `_submitted_NEUCOM-D-26-20952_2026-09-16/` = **投出去的那一版原件**，
  **永久保留**（被拒稿也必须留底，否则历史不可复核）。
- **不要**用它当当前投稿件——当前件在 **`../A1_NeuralNetworks/`**。
- 本目录**不应**再被任何投稿流程引用。

## 后继

→ `../A1_NeuralNetworks/`
""",
    "A23_JOE": """# A23 → IEEE Journal of Oceanic Engineering（**在审**）

| 项 | 内容 |
|---|---|
| 稿件 | `paper_a2/` |
| 稿号 | **`26-0663`** |
| 状态 | 🔄 **Received（2026-09-21 系统时间）** |
| 前史 | Ocean Engineering `OE-D-26-11643` **桌面拒（2026-09-18）** |
| 页数 | 66 页（`main.tex`）/ 64 页（`main_ieee.tex`） |

## 目录结构

| 路径 | 用途 |
|---|---|
| `A23_latex_source.zip` | LaTeX 源码包（投稿用） |
| `abstract_plaintext.txt` | 摘要纯文本 |
| `supplementary/` | **给审稿人的补充材料**（含同期稿件的 PDF 与决定信，供披露同出版商关系） |
| `current/` | **当前最新投稿件**（来自 `paper_a2/`，2026-10-06 复制） |

## ⚠️ 注意

- 本稿**在审中** → 不得再投他处。
- `supplementary/` 内含有 **A1（`NEUCOM-D-26-20952`）**、**P1（`PR-D-26-10149`）** 的 PDF
  与 **OE `OE-D-26-11643` 的决定信** —— 这是**主动披露同出版商/同期关系**用的，
  **保留**；但请注意其中 A1 与 P1 的**状态已变**（A1 桌面拒、P1 已被拒），
  若编辑追问应据实说明。
- 中文版（`main_zh.*`）**不上传**。
""",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    for name, text in TEXTS.items():
        p = SUB / name / "README.md"
        if p.exists():
            print(f"  ⚠️ {name}/README.md 已存在，跳过")
            continue
        p.write_text(text, encoding="utf-8")
        print(f"  ✅ {name}/README.md 已写")
    # 核验
    print()
    for d in sorted(SUB.iterdir()):
        if d.is_dir():
            print(f"  {d.name:<48} README {'✅' if (d / 'README.md').exists() else '🔴'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
