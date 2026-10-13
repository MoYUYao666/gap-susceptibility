# -*- coding: utf-8 -*-
r"""把三份回复转为 **EM 纯文本框可直接粘贴**的版本（2026-10-13）。

## 为什么必须转

EM 的 "Response to Reviewers" 输入框是**纯文本**。当前文本含 LaTeX 记号：

| 现状 | 粘贴后会显示 | 应显示 |
|---|---|---|
| `$3.09\times$` | `$3.09\times$` | `3.09x` |
| `$\|\nabla E\|^2$` | `$\|\nabla E\|^2$` | `norm(grad E)^2` |
| `$\Gamma$-guided` | `$\Gamma$-guided` | `Gamma-guided` |
| `$7{,}237{,}632$` | `$7{,}237{,}632$` | `7,237,632` |
| `**bold**` | `**bold**` | `bold` |
| `*italic*` | `*italic*` | `italic` |

**⇒ 生成 `_plain.txt` 三个版本**（Markdown 版仍保留，供 PDF/Word 版回复信使用）。

## 转换规则（保守：只去标记，不改语义）

1. `$...$` → 内部按符号表替换（`\times`→`x`、`\Gamma`→`Gamma`、`\Delta`→`Delta`、
   `\|`→`norm`、`\nabla`→`grad`、`\pm`→`+/-`、`\leq`→`<=`、`\geq`→`>=`、`\in`→`in`、
   `{,}`→`,`、`\`→`` 等）
2. `**X**` → `X`；`*X*` → `X`；`` `X` `` → `X`
3. 去 LaTeX 转义：`\%`→`%`、`\_`→`_`、`\&`→`&`
4. 断言：**输出中不含 `$`、`\`、`**`**

    python tools\_p548_plaintext_responses.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTDIR = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"

SYMS = [
    (r"\\times", "x"), (r"\\Gamma", "Gamma"), (r"\\Delta", "Delta"),
    (r"\\nabla", "grad"), (r"\\beta", "beta"), (r"\\eta", "eta"),
    (r"\\alpha", "alpha"), (r"\\sigma", "sigma"), (r"\\mu", "mu"),
    (r"\\pm", "+/-"), (r"\\leq", "<="), (r"\\geq", ">="), (r"\\approx", "~="),
    (r"\\in\b", "in"), (r"\\to\b", "->"), (r"\\cdot", "."), (r"\\sum", "sum"),
    (r"\\\\\|", "norm"), (r"\\langle", "<"), (r"\\rangle", ">"),
    (r"\{,\}", ","), (r"\\%", "%"), (r"\\_", "_"), (r"\\&", "&"),
    (r"\\emph", ""), (r"\\textbf", ""), (r"\\noindent", ""), (r"\\ref", ""),
    (r"\\mathcal\{([^}]*)\}", r"\1"), (r"\\mathrm\{([^}]*)\}", r"\1"),
    (r"\\text\{([^}]*)\}", r"\1"), (r"\\le\b", "<="), (r"\\ge\b", ">="),
    (r"\\times10", "x10"), (r"\\sim", "~"), (r"\\ ", " "),
]


def to_plain(t: str) -> str:
    # 0) 去重复标签
    t = t.replace("**Response:** **Response.** ", "**Response:** ")
    t = t.replace("**Response:** **Response.**", "**Response:**")
    # 1) $...$ 内部
    def math(m):
        s = m.group(1)
        for pat, rep in SYMS:
            s = re.sub(pat, rep, s)
        s = s.replace("\\", "").replace("{", "").replace("}", "")
        s = re.sub(r"\s+", " ", s).strip()
        return s
    t = re.sub(r"\$([^$]*)\$", math, t)
    # 2) 剩餘数学环境名
    for pat, rep in SYMS:
        t = re.sub(pat, rep, t)
    # 3) Markdown 强调
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    # 4) 残留转义
    t = t.replace("\\", "")
    # 5) 空格整理
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    srcs = sorted(OUTDIR.glob("P3_RESPONSE_Reviewer*.txt"))
    srcs = [p for p in srcs if "_plain" not in p.name]
    print(f"  找到 {len(srcs)} 份（Markdown 版）")
    if not srcs:
        print("  🔴 先跑 tools/_p547_make_three_responses.py")
        return 1
    ok = True
    for p in srcs:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        plain = to_plain(t)
        bad = {k: plain.count(k) for k in ("$", "\\", "**") if plain.count(k)}
        print(f"  {p.name:<34} {len(t):>7,} → {len(plain):>7,} 字符"
              f" ｜ 残留标记 {bad if bad else '无'}")
        if bad:
            ok = False
        if a.apply:
            outp = OUTDIR / (p.stem + "_plain.txt")
            io.open(outp, "w", encoding="utf-8", newline="").write(plain)
    print()
    if a.apply:
        print("  复核（_plain 版）：")
        for p in sorted(OUTDIR.glob("*_plain.txt")):
            t = io.open(p, encoding="utf-8", errors="replace").read()
            n_pt = len(re.findall(r"^\*\*Point |^Point ", t, re.M))
            has = {k: t.count(k) for k in ("$", "\\", "**") if t.count(k)}
            print(f"    {p.name:<40} Point {n_pt:>2} ｜ 残留 {has if has else '无'}")
    print()
    print(f"  **判定：{'✅ 无残留标记' if ok else '🔴 仍有残留，需补规则'}**")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
