# -*- coding: utf-8 -*-
r"""修正字面 `\n` 的检测与修复判据；落账 `_p501` 事故（2026-10-13）。

## 🔴 我的第 29 个错（`_p501` 造成真实损伤）

**意图**：把 Python 原始字符串写进 `.tex` 造成的**字面 `\n`**（反斜杠+n）换成真换行。
**实际**：判据 `re.sub(r"\\n[ \t]*(?=\r?\n)", "", text)` **同时匹配了合法的 LaTeX 命令**
—— 任何"整行以 `\n` 开头"的行（如 `\newtheorem{...}`），其 `\n` 被删 ⇒

    \newtheorem{theorem}{Theorem}[section]   →   （空行）ewtheorem{theorem}{Theorem}[section]

**⇒ 10 处 `\newtheorem` 断头（`main.tex` 5 + `supplementary.tex` 5），编译错误 10 → 13。**
**已用 `edit` 工具精确修复**（逐处字面替换），现 **13 页 / 0 错 / 0 未定义 / 全稿 0 断头**。

## 正确的判据（本脚本实现）

**字面 `\n` 的特征：`\` + `n` 后面**不是字母**（即不构成 LaTeX 命令名）。**
- ✅ 修复：`\n` 后跟空白/行尾/非字母 ⇒ 字面，替换为真换行
- ❌ 不动：`\n` 后跟字母（`\newtheorem`、`\newcommand`、`\not`、`\nabla`、`\neq`…）⇒ **合法命令**

**⚠️ 教训（本阶段第 3 次同型）**：**判据过宽的正则替换比不做更危险。**
前两次：`_p433`（21 处）、`_p435`；本次 `_p501`。**⇒ 凡涉及"批量替换 tex"，必须先 dry-run + 断言"合法命令未被触碰"。**

    python tools\_p503_fix_literal_n_correct.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"

# 字面 \n：反斜杠 + n，且其后**不是字母**
LITERAL_N = re.compile(r"\\n(?![A-Za-z])")
# 合法 LaTeX 命令里以 \n 开头的（用于断言"未被触碰"）
LEGIT = re.compile(r"\\n[A-Za-z]+")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(glob.glob(str(PI / "sections" / "*.tex"))) + \
        sorted(glob.glob(str(PI / "*.tex"))) + \
        sorted(glob.glob(str(PI / "supplementary" / "*.tex")))
    files = [f for f in files if ".bak" not in os.path.basename(f)]
    print("=" * 100)
    print("按**修正判据**检查（字面 \\n = \\n 后不跟字母）")
    print("=" * 100)
    total_lit = total_legit = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        lit = LITERAL_N.findall(t)
        legit = sorted(set(LEGIT.findall(t)))
        total_lit += len(lit)
        total_legit += len(LEGIT.findall(t))
        if lit or legit:
            print(f"  {os.path.relpath(f, PI):<42} 字面 \\n {len(lit):>3} ｜ "
                  f"合法 \\n-命令 {len(legit):>3} {legit[:8] if legit else ''}")
    print()
    print(f"  **全稿字面 \\n = {total_lit}** ｜ **合法 \\n-命令 = {total_legit}**（后者**不可触碰**）")

    if total_lit == 0:
        print("  ✅ 无可修项（`_p435` 之后已清干净）")
        return 0
    if not a.apply:
        print("  （预演）—— 未写入")
        return 0
    fixed = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        n_before_lit = len(LITERAL_N.findall(t))
        n_before_legit = len(LEGIT.findall(t))
        if not n_before_lit:
            continue
        t2 = LITERAL_N.sub("\n", t)
        # 🔴 关键断言：合法命令数量必须**不变**
        n_after_legit = len(LEGIT.findall(t2))
        assert n_after_legit == n_before_legit, \
            f"[判据越界] {os.path.basename(f)}: 合法 \\n-命令 {n_before_legit} → {n_after_legit}"
        io.open(f, "w", encoding="utf-8", newline="").write(t2)
        fixed += n_before_lit
        print(f"  ✅ {os.path.relpath(f, PI):<42} 修 {n_before_lit} 处（合法命令 {n_before_legit} 未动）")
    print(f"  → 共修 {fixed} 处；**断言全部通过**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
