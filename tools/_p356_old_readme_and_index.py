# -*- coding: utf-8 -*-
r"""写 `SUBMISSION/_old/README.md` 并更新 `SUBMISSION/README.md` 总索引（2026-10-12）。

    python tools\_p356_old_readme_and_index.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUB = REPO / "SUBMISSION"
OLD = SUB / "_old"

OLD_README = """# `_old/` —— 已失效的旧投稿（**只作历史存档**）

> 整理时间：{ts}
> 判定依据：**投稿状态**（已拒稿 / 已被新目标取代），**不是**时间新旧。

| 目录 | 稿件 | 期刊 | 稿号 | 失效原因 | 文件数 |
|---|---|---|---|---|---|
| `A1_Neurocomputing/` | A1 | Neurocomputing | `NEUCOM-D-26-20952` | 🔴 **桌面拒（2026-10-10）**，无审稿意见；已被 `../A1_NeuralNetworks/` 取代 | {n1} |
| `A23_OceanEngineering/` | A23 | Ocean Engineering | `OE-D-26-11643` | 🔴 **桌面拒（2026-09-18）**；已被 `../A23_JOE/` 取代 | {n2} |
| `P1_PatternRecognition/` | P1 | Pattern Recognition | `PR-D-26-10149` | 🔴 **已被拒**（操作者 2026-10-12 确认） | {n3} |

## ⚠️ 使用规则

1. **这里的文件一律不得当作当前投稿件使用。**
2. **不得删除**——被拒稿的每一版都必须留底，否则一旦需要复核"当时投的是什么"就没有依据。
3. `A1_Neurocomputing/_submitted_NEUCOM-D-26-20952_2026-09-16/` 是**投出去的那一版原件**
   （归档时由整理脚本从该目录根移入）。
4. 后继稿件：

| 旧 | 新 |
|---|---|
| `A1_Neurocomputing/` | → `../A1_NeuralNetworks/`（Elsevier ATS 转投，**须 2026-11-08 23:59 前确认**） |
| `A23_OceanEngineering/` | → `../A23_JOE/`（`26-0663`，在审） |
| `P1_PatternRecognition/` | → 无后继（P1 已终止）；其内容已演进为 `../PaperA_Neurocomputing/`（P1+P2 合并稿，**尚未投稿**） |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0

    def n(d):
        p = OLD / d
        return len([x for x in p.rglob("*") if x.is_file()]) if p.exists() else 0

    (OLD / "README.md").write_text(
        OLD_README.format(ts=time.strftime("%Y-%m-%d %H:%M"),
                          n1=n("A1_Neurocomputing"), n2=n("A23_OceanEngineering"),
                          n3=n("P1_PatternRecognition")), encoding="utf-8")
    print("  ✅ _old/README.md 已写")

    # 更新总索引
    p = SUB / "README.md"
    t = io.open(p, encoding="utf-8").read()
    old_tbl = t[t.find("## 状态总表"):t.find("## 各目录内均有")]
    new_tbl = """## 状态总表（根目录 = **当前在用**）

| 目录 | 稿件 | 期刊 | 稿号 | 状态 | 页数 |
|---|---|---|---|---|---|
| `A1_NeuralNetworks/` | **A1** | Neural Networks | —（未投） | ⚠️ **ATS 转投须 2026-11-08 23:59 前确认** | 42 |
| `PaperA_Neurocomputing/` | **Paper A**（P1+P2） | Neurocomputing | —（未投） | ✅ 就绪；PR 意见 26/26 已改入；**待定投稿时点** | 60 / 44 |
| `P3_PRL/` | P3 | Pattern Recognition Letters | `PRLETTERS-D-26-02378` | 🔄 **在审** | 11 |
| `Review_PRL/` | 综述 Commentary | Pattern Recognition Letters | `PRLETTERS-D-26-02402` | 🔄 **在审** | 7 |
| `A23_JOE/` | A23 | IEEE JOE | `26-0663` | 🔄 Received（2026-09-21） | 66 |

## 已失效的旧投稿 → `_old/`（**只作历史存档**）

| 目录 | 稿件 | 期刊 | 稿号 | 失效原因 |
|---|---|---|---|---|
| `_old/A1_Neurocomputing/` | A1 | Neurocomputing | `NEUCOM-D-26-20952` | 🔴 桌面拒（2026-10-10） |
| `_old/A23_OceanEngineering/` | A23 | Ocean Engineering | `OE-D-26-11643` | 🔴 桌面拒（2026-09-18） |
| `_old/P1_PatternRecognition/` | P1 | Pattern Recognition | `PR-D-26-10149` | 🔴 已被拒 |

→ 详见 `_old/README.md`。**`_old/` 内文件一律不得当作当前投稿件使用，也不得删除。**

"""
    if "## 已失效的旧投稿" not in t:
        t = t.replace(old_tbl, new_tbl)
        io.open(p, "w", encoding="utf-8", newline="").write(t)
        print("  ✅ 总索引已更新")
    else:
        print("  总索引已含 _old 段")

    # 核验
    print()
    for d in sorted(SUB.iterdir()):
        if d.is_dir():
            cnt = len([x for x in d.rglob("*") if x.is_file()])
            print(f"  {d.name:<48} {cnt:>3} 文件 ｜ README "
                  f"{'✅' if (d / 'README.md').exists() else '🔴'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
