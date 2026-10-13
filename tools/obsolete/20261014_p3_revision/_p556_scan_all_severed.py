# -*- coding: utf-8 -*-
r"""全仓库扫描并修复"断头命令"（2026-10-13）。

## 背景

`_p515` 只扫了 `paper3/paper_ieee/` 下的 11 个 tex —— **漏了**：
- `title_page_prl.tex`（本次发现 `\noindent` → `oindent`）
- `PRL_submission/`
- `SUBMISSION/` 下的包

**⇒ 本脚本扫全仓库**（排除 `.bak`），判据同 `_p515`：
**行首 token 命中白名单 且 前一行"表达式没写完"**（`$` 未闭合或以 `( [ | = , \langle \|` 结尾）。

**⚠️ 白名单补充**：`oindent`（`\noindent`）、`abla`（`\nabla`）、`eq`（`\neq`）、
`ot`（`\not`）、`onumber`、`ewline`、`eg`、`orm`。

    python tools\_p556_scan_all_severed.py [--apply]
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
         "orm": "norm", "othing": "nothing", "ewpage": "newpage"}
UNFINISHED = ("$", "(", "[", "|", "=", ",", "\\langle", "\\|", "\\perp",
              "\\cos(", "\\Gamma", "{", "\\sim", "\\approx", "\\pm", "\\to", "\\text")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = [p for p in REPO.rglob("*.tex")
             if ".bak" not in p.name and "obsolete" not in str(p).lower()]
    print(f"  扫描 {len(files)} 个 tex（全仓库，排除 .bak 与 obsolete）")
    print()
    plan = []
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        lines = t.split("\n")
        hits = []
        for i, ln in enumerate(lines):
            m = re.match(r"^([a-z]{1,10})\b", ln)
            if not m or m.group(1) not in FIXES:
                continue
            prev = lines[i - 1].rstrip() if i >= 1 else ""
            if any(prev.endswith(x) for x in UNFINISHED) or prev.count("$") % 2 == 1:
                hits.append((i, m.group(1)))
        if hits:
            plan.append((f, hits))
            print(f"  🔴 {f.relative_to(REPO)}（{len(hits)} 处）")
            for i, tok in hits[:6]:
                print(f"       L{i+1}: 「{tok}」→ 应 \\{FIXES[tok]}")
    print()
    total = sum(len(h) for _, h in plan)
    print(f"  ⇒ 合计 {total} 处")
    if not plan:
        print("  ✅ 无")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    done = 0
    for f, hits in plan:
        lines = io.open(f, encoding="utf-8", errors="replace").read().split("\n")
        before = "\n".join(lines)
        for i, tok in hits:
            lines[i] = "\\" + FIXES[tok] + lines[i][len(tok):]
        after = "\n".join(lines)
        delta = len(after) - len(before)
        assert delta == 2 * len(hits), f"[判据越界] {f.name}: Δ{delta} ≠ 2×{len(hits)}"
        bak = f.with_suffix(f.suffix + ".bak_p556")
        if not bak.exists():
            shutil.copy2(f, bak)
        io.open(f, "w", encoding="utf-8", newline="").write(after)
        done += len(hits)
        print(f"  ✅ {str(f.relative_to(REPO)):<56} 修 {len(hits)} 处")
    print(f"  → 共修 {done} 处（**断言全部通过**）")
    # 复核
    left = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        lines = t.split("\n")
        for i, ln in enumerate(lines):
            m = re.match(r"^([a-z]{1,10})\b", ln)
            if not m or m.group(1) not in FIXES:
                continue
            prev = lines[i - 1].rstrip() if i >= 1 else ""
            if any(prev.endswith(x) for x in UNFINISHED) or prev.count("$") % 2 == 1:
                left += 1
    print(f"  复核：全仓库残留 {left} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
