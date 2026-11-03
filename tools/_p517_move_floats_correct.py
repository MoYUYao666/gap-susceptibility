# -*- coding: utf-8 -*-
r"""从备份恢复 `experiments.tex`，并**按正确映射**移出表/图（2026-10-13）。

## 我的 `_p516` 错在哪（第 31 个错）

| 错 | 说明 |
|---|---|
| **① label↔环境 映射错** | 我把 `tab:sample` 映射到 `table`，实际它属于 **L27-46 的 `table*`**（`table*` 与 `table` 是两个不同环境） |
| **② 留孤儿 `\end{figure*}`** | 用 `figure` 的正则捕获 `figure*` 的内容（非贪婪），`\end{figure*}` 未被覆盖 ⇒ **未闭合环境** ⇒ **19 个错误** |
| **③ 正则不够稳** | 应当**按 `\begin{X}` … `\end{X}` 配对扫描**，而不是两套独立正则 |

**⇒ 已从 `.bak_p516` 完整恢复，本脚本重做。**

## 正确做法

1. **配对扫描**：对每个 `\begin{X}`，找**同名的第一个 `\end{X}`**（`X` 含 `*`）⇒ 精确区间；
2. **按环境内实际的 `\label`** 决定移出哪一块（**不预设映射**）；
3. **移出后断言**：残余 `\begin{X}` 与 `\end{X}` 数量**必须相等**。

    python tools\_p517_move_floats_correct.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
EX = PI / "sections" / "experiments.tex"
BAK = PI / "sections" / "experiments.tex.bak_p516"
SUP = PI / "supplementary" / "supplementary.tex"


def scan_floats(t: str):
    """配对扫描所有 float 环境，返回 [(name, start, end, label)]。"""
    out = []
    for m in re.finditer(r"\\begin\{(table\*?|figure\*?)\}", t):
        name = m.group(1)
        e = t.find(f"\\end{{{name}}}", m.end())
        if e < 0:
            print(f"  🔴 {name} @ {m.start()} 无配对 \\end{{{name}}}")
            continue
        blk = t[m.start():e + len(f"\\end{{{name}}}")]
        labs = re.findall(r"\\label\{([^}]*)\}", blk)
        out.append((name, m.start(), e + len(f"\\end{{{name}}}"), labs[0] if labs else None))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not BAK.exists():
        print(f"  🔴 缺备份 {BAK}")
        return 1
    # ① 先恢复
    ex_bak = io.open(BAK, encoding="utf-8", errors="replace").read()
    cur = io.open(EX, encoding="utf-8", errors="replace").read()
    print(f"  备份 {len(ex_bak):,} ｜ 当前（损坏）{len(cur):,}")

    floats = scan_floats(ex_bak)
    print()
    print("  配对扫描结果（备份中）：")
    for name, i, j, lab in floats:
        print(f"     {name:<9} L{ex_bak[:i].count(chr(10))+1:<5} label={lab}  长度 {j-i:,}")

    # ② 计划移出（按 label 决定）
    MOVE = {"tab:sample", "tab:phase", "fig:phase_transition", "fig:counterfactual"}
    plan = [f for f in floats if f[3] in MOVE]
    print()
    print(f"  计划移出 {len(plan)} 个（按 label）：{[p[3] for p in plan]}")
    saved = sum(j - i for _, i, j, _ in plan)
    print(f"  ⇒ 省 {saved:,} 字符")

    if not a.apply:
        print("  （预演）")
        return 0

    t = ex_bak
    add = []
    for name, i, j, lab in sorted(plan, reverse=True):
        add.insert(0, (lab, t[i:j]))
        t = t[:i] + t[j:]
    # 引用 → 显式补充编号
    MAP = {"tab:phase": "Supplementary Table~S1", "fig:phase_transition": "Supplementary Figure~S1",
           "fig:counterfactual": "Supplementary Figure~S2", "tab:sample": "Supplementary Table~S2"}
    for lab, txt in MAP.items():
        t = t.replace(rf"\ref{{{lab}}}", txt)

    # ③ 断言：begin/end 必须配平
    for name in ("table", "table*", "figure", "figure*"):
        nb = len(re.findall(rf"\\begin\{{{re.escape(name)}\}}", t))
        ne = len(re.findall(rf"\\end\{{{re.escape(name)}\}}", t))
        ok = (nb == ne)
        print(f"  {'✅' if ok else '🔴'} {name:<8} begin {nb} ｜ end {ne}")
        assert ok, f"[环境不配平] {name}: begin {nb} vs end {ne}"

    bak = EX.with_suffix(".tex.bak_p517")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)
    print(f"  ✅ experiments.tex {len(ex_bak):,} → {len(t):,}")

    sup = io.open(SUP, encoding="utf-8", errors="replace").read()
    # 去掉上一轮误加的 "Tables and Figures" 段（若存在）
    k = sup.find("\\section{Tables and Figures}")
    if k > 0:
        e = sup.find("\\bibliographystyle{IEEEtran}")
        sup = sup[:k] + sup[e:]
        print("  ✅ 已移除上一轮误加的 Tables and Figures 段")
    addtxt = ["\n\n\\section{Tables and Figures}\n",
              "Kept here so that the main text can meet the journal's page limit; each is "
              "cited from the main text by its number below.\n"]
    for lab, blk in add:
        addtxt.append(f"\n% ---- {lab} ----\n{blk}\n")
    sup2 = sup.replace("\\bibliographystyle{IEEEtran}", "".join(addtxt) + "\n\\bibliographystyle{IEEEtran}")
    io.open(SUP, "w", encoding="utf-8", newline="").write(sup2)
    print(f"  ✅ supplementary {len(sup):,} → {len(sup2):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
