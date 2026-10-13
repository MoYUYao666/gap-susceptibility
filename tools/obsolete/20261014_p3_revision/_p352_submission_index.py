# -*- coding: utf-8 -*-
r"""写 `SUBMISSION/README.md` 总索引（2026-10-12）。

    python tools\_p352_submission_index.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUB = REPO / "SUBMISSION"

ROWS = [
    ("`A1_NeuralNetworks/`", "**A1**", "Neural Networks", "—（未投）",
     "⚠️ **ATS 转投须 2026-11-08 23:59 前确认**", "42 页"),
    ("`A1_Neurocomputing/_submitted_NEUCOM-D-26-20952_2026-09-16/`", "A1（历史版）",
     "Neurocomputing", "`NEUCOM-D-26-20952`", "🔴 **桌面拒（2026-10-10）**", "41 页"),
    ("`PaperA_Neurocomputing/`", "**Paper A**（P1+P2）", "Neurocomputing", "—（未投）",
     "✅ 就绪；PR 意见 26/26 已改入；**待定投稿时点**", "60 / 44 页"),
    ("`P1_PatternRecognition/`", "P1", "Pattern Recognition", "`PR-D-26-10149`",
     "🔴 **已被拒**（2026-10-12 操作者确认）", "—"),
    ("`P3_PRL/`", "P3", "Pattern Recognition Letters", "`PRLETTERS-D-26-02378`",
     "🔄 **在审**", "11 页"),
    ("`Review_PRL/`", "综述 Commentary", "Pattern Recognition Letters",
     "`PRLETTERS-D-26-02402`", "🔄 **在审**", "7 页"),
    ("`A23_JOE/`", "A23", "IEEE JOE", "`26-0663`", "🔄 Received（2026-09-21）", "66 页"),
    ("`A23_OceanEngineering/`", "A23（历史版）", "Ocean Engineering",
     "`OE-D-26-11643`", "🔴 **桌面拒（2026-09-18）**", "—"),
]

NOTES = """
## 命名规则

- **`<稿>-<刊>/`**：一稿一号一目录。
- **`_submitted_<稿号>_<日期>/`**：**已投出的那一版原件永久归档**，不得覆盖
  （否则一旦被拒，历史版本不可复核）。
- 目录根的散文件 = **当前最新投稿件**。
- `current/`：某些稿（如 A23）把最新件收在 `current/` 下，与历史版区分。

## 状态总表
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0

    lines = ["# 投稿包索引（`SUBMISSION/`）", "",
             f"> 整理时间：**{time.strftime('%Y-%m-%d %H:%M')}**",
             "> 规则：**一稿一稿号一目录**；已投出的版本永久归档为 "
             "`_submitted_<稿号>_<日期>/`。", "",
             "## 状态总表", "",
             "| 目录 | 稿件 | 期刊 | 稿号 | 状态 | 页数 |",
             "|---|---|---|---|---|---|"]
    for d, ms, j, num, st, pg in ROWS:
        lines.append(f"| {d} | {ms} | {j} | {num} | {st} | {pg} |")
    lines += ["", "## 各目录内均有 `README.md`（文件清单 + 重编译方法 + 投稿前注意事项）", "",
              "## 来源映射（投稿件从哪来）", "",
              "| 目录 | 生成来源 |", "|---|---|",
              "| `A1_NeuralNetworks/` | `paper_a1/`（2026-10-12 02:06） |",
              "| `PaperA_Neurocomputing/` | `paper合/NC_submission/`（2026-10-12 16:03） |",
              "| `P3_PRL/` | `paper3/paper_ieee/PRL_submission/`（2026-09-29） |",
              "| `Review_PRL/` | `paper_review_prl/`（2026-10-06） |",
              "| `A23_JOE/current/` | `paper_a2/`（2026-10-06） |", "",
              "## ⚠️ 投稿前必读", "",
              "1. **A1 的 ATS 转投有截止日：2026-11-08 23:59**。",
              "2. **Paper A 从未投稿**；投出前须在 cover letter 披露与 A1 的关系"
              "（同为 Elsevier，主题相关）。",
              "3. **P3（`-02378`）与综述（`-02402`）在审中** → **不得**再投他处；"
              "`paper_ap3/` 因含 P3 内容而**不可投**。",
              "4. **中文版（`main_zh.*`）一律不上传**（保守做法；JOE 的认证覆盖\"任何语言\"）。",
              "5. 已拒稿的目录（`*_submitted_*`、`P1_PatternRecognition`）**只作历史存档**，"
              "里面的文件**不得**当作当前投稿件使用。", "",
              "## 重建方式", "",
              "```powershell",
              "python tools\\_p350_organize_submission.py --apply   # A1",
              "python tools\\_p351_organize_submission2.py --apply  # Paper A / P3 / 综述 / A23",
              "python tools\\_p352_submission_index.py --apply      # 本索引",
              "```", ""]

    (SUB / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print("  ✅ SUBMISSION/README.md 已写")

    # 核验
    print()
    print("=" * 96)
    print("核验")
    print("=" * 96)
    for d in sorted(SUB.iterdir()):
        if not d.is_dir():
            continue
        files = [p for p in d.rglob("*") if p.is_file()]
        newest = max((p.stat().st_mtime for p in files), default=0)
        has = (d / "README.md").exists()
        print(f"  {d.name:<48} {len(files):>4} 文件 ｜ README {'✅' if has else '🔴'} ｜ "
              f"最新 {time.strftime('%m-%d %H:%M', time.localtime(newest))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
