# -*- coding: utf-8 -*-
r"""加强断头命令判据：`oindent`/`abla` 后紧跟命令或大写字母即为断头（2026-10-14）。

## 我先前判据的漏洞（第 34 个错）

`_p556` 的判据是：**行首 token 命中白名单 且 前一行"表达式没写完"**。
但 `title_page_prl.tex` 里的写法是：

```
\vspace{1em}

oindent\textbf{Author}\        ← 前一行是 \vspace{1em}，不以 $ / ( 结尾
Hongrui Wan\
```

**⇒ 前一行是 `\vspace{1em}` ⇒ 判据不成立 ⇒ 漏检 7 处。**
而 PDF 里已经印出 **`oindentAuthor`**。

## 加强判据（补一条，与旧判据取"或"）

**`oindent` / `abla` 等断头 token 后面紧跟 LaTeX 命令（`\`）或大写字母开头单词 ⇒ 必为断头**
—— 因为在 LaTeX 里 `oindent\textbf{...}` 这种写法**永远不合法**（`oindent` 不是任何命令）。

    python tools\_p564_stronger_severed_check.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FIXES = {"abla": "nabla", "oindent": "noindent", "eq": "neq", "ot": "not",
         "onumber": "nonumber", "ewline": "newline", "eg": "neg",
         "orm": "norm", "othing": "nothing", "ewpage": "newpage",
         "ewtheorem": "newtheorem", "ewcommand": "newcommand"}

# 判据 A：前一行"表达式没写完"
UNFINISHED = ("$", "(", "[", "|", "=", ",", "\\langle", "\\|", "\\perp",
              "\\cos(", "\\Gamma", "{", "\\sim", "\\approx", "\\pm", "\\to", "\\text")
# 判据 B：断头 token 后紧跟 `\`（命令）或大写字母
CRIT_B = re.compile(r"^(abla|oindent|eq|ot|onumber|ewline|eg|orm|othing|ewpage|ewtheorem|ewcommand)"
                    r"(\\|[A-Z])")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = [p for p in REPO.rglob("*.tex")
             if ".bak" not in p.name and "obsolete" not in str(p).lower()]
    print(f"  扫描 {len(files)} 个 tex（判据 A 或 B）")
    print()
    plan = []
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        lines = t.split("\n")
        hits = []
        for i, ln in enumerate(lines):
            m = re.match(r"^([a-z]{1,12})\b", ln)
            if not m or m.group(1) not in FIXES:
                continue
            tok = m.group(1)
            prev = lines[i - 1].rstrip() if i >= 1 else ""
            condA = any(prev.endswith(x) for x in UNFINISHED) or prev.count("$") % 2 == 1
            condB = bool(CRIT_B.match(ln))
            if condA or condB:
                hits.append((i, tok, "A" if condA and not condB else ("B" if condB and not condA else "A+B")))
        if hits:
            plan.append((f, hits))
            print(f"  🔴 {f.relative_to(REPO)}（{len(hits)} 处）")
            for i, tok, why in hits[:8]:
                print(f"       L{i+1}: 「{tok}」({why}) → \\{FIXES[tok]}")
    total = sum(len(h) for _, h in plan)
    print()
    print(f"  ⇒ 合计 {total} 处")
    if not total:
        print("  ✅ 无")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    done = 0
    for f, hits in plan:
        lines = io.open(f, encoding="utf-8", errors="replace").read().split("\n")
        before = "\n".join(lines)
        for i, tok, _ in hits:
            lines[i] = "\\" + FIXES[tok] + lines[i][len(tok):]
        after = "\n".join(lines)
        delta = len(after) - len(before)
        assert delta == 2 * len(hits), f"[判据越界] {f.name}: Δ{delta} ≠ 2×{len(hits)}"
        bak = f.with_suffix(f.suffix + ".bak_p564")
        if not bak.exists():
            shutil.copy2(f, bak)
        io.open(f, "w", encoding="utf-8", newline="").write(after)
        done += len(hits)
        print(f"  ✅ {str(f.relative_to(REPO)):<58} 修 {len(hits)} 处")
    print(f"  → 共修 {done} 处（断言全部通过）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
