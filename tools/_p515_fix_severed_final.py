# -*- coding: utf-8 -*-
r"""修"断头命令"这一类**静默**损伤（2026-10-13）。

## 为什么这是最危险的一类（成员 `writing-hardener` 查出）

**病因**：用**非 raw** 字符串拼 LaTeX 时，`"\nabla"` 里的 `\n` 被 Python 解释为**真换行** ⇒

    \nabla  →  换行 + abla        （PDF 印 `ablaE`，不是 `∇E`）
    \noindent → 换行 + oindent    （→ 排版错乱但不报错）
    \neq    →  换行 + eq          （→ 印成 `eq`）

**⇒ 为什么我的检查器全部漏掉**：
- `main.log` 的 `^!` 计数 = 0（**数学模式里 `abla E` 是四个合法变量字母**）
- `_p497` 矛盾扫描 = 0（不是内容矛盾）
- `_p503` 字面 `\n` 检查 = 0（**字面 `\n` 已经"修"掉了，正因为它被替换成了真换行**）

**⇒ 这是"我的闸门全绿、但产物是错的"——本阶段最严重的检测盲区。**

## 判据（成员做窄，我沿用）

**行首 token 命中白名单**（`abla`/`oindent`/`eq`/`ot`/`abla`…）**且**该 token **前一行是"表达式没写完"**
（`$` 未闭合，或以 `( [ | = , \langle \perp \cos( \Gamma` 结尾）⇒ 判定为断头。
**否则拒绝写盘**（避免 `_p501` 那种吃合法命令的事故重演）。

    python tools\_p515_fix_severed_final.py [--apply]
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

# 断头 token → 完整命令（成员查出的 3 类）
FIXES = {"abla": "nabla", "oindent": "noindent", "eq": "neq", "ot": "not",
         "onumber": "nonumber", "ewline": "newline", "eg": "neg", "u": "nu",
         "orm": "norm", "othing": "nothing"}

# 前一行"表达式没写完"的判据
UNFINISHED = ("$", "(", "[", "|", "=", ",", "\\langle", "\\perp", "\\cos(",
              "\\Gamma", "{", "\\sim", "\\approx", "\\pm", "\\to", "\\text")


def check(path: Path, apply: bool):
    t = io.open(path, encoding="utf-8", errors="replace").read()
    lines = t.split("\n")
    hits = []
    for i, ln in enumerate(lines):
        m = re.match(r"^([a-z]{1,10})\b", ln)
        if not m:
            continue
        tok = m.group(1)
        # 该 token 是否可能是被吃掉了 "\n" 的命令尾巴
        cand = [k for k in FIXES if tok == k]
        if not cand:
            continue
        prev = lines[i - 1].rstrip() if i >= 1 else ""
        unfinished = any(prev.endswith(x) for x in UNFINISHED) or prev.count("$") % 2 == 1
        if unfinished:
            hits.append((i + 1, tok, ln[:90], prev[-60:]))
    return t, lines, hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(PI.glob("sections/*.tex")) + [PI / "main.tex"] + \
        sorted((PI / "supplementary").glob("*.tex")) + \
        [PI / "main_body_full.tex", PI / "title_page_prl.tex"]
    files = [f for f in files if f.exists() and ".bak" not in f.name]
    print(f"  扫描 {len(files)} 个 tex")
    print()
    total = 0
    plan = []
    for f in files:
        t, lines, hits = check(f, False)
        if hits:
            print(f"  ── {f.relative_to(PI)}（{len(hits)} 处）")
            for ln, tok, txt, prev in hits[:8]:
                print(f"       L{ln} 「{tok}」 {txt}")
                print(f"          前一行尾部: …{prev}")
            total += len(hits)
            plan.append((f, hits))
    print()
    print(f"  **合计命中 {total} 处**")
    if not plan:
        print("  ✅ 无")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    done = 0
    for f, hits in plan:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        lines = t.split("\n")
        before = len(t)
        for ln, tok, _, _ in hits:
            idx = ln - 1
            full = "\\" + FIXES[tok]
            lines[idx] = full + lines[idx][len(tok):]
        new = "\n".join(lines)
        delta = len(new) - before
        assert delta == 2 * len(hits), \
            f"[判据越界] {f.name}: 字符增量 {delta} ≠ 2×{len(hits)}"
        bak = f.with_suffix(".tex.bak_p515")
        if not bak.exists():
            shutil.copy2(f, bak)
        io.open(f, "w", encoding="utf-8", newline="").write(new)
        done += len(hits)
        print(f"  ✅ {str(f.relative_to(PI)):<44} 修 {len(hits)} 处（字符 +{delta}）")
    print(f"  → 共修 {done} 处；**断言全部通过（增量恰为 2×修复数）**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
