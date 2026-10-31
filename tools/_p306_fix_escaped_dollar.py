# -*- coding: utf-8 -*-
r"""修 `_p305` 写入时把 `$` 转义成 `\$` 的问题（2026-10-12）。

## 病因

`_p305` 的 TRIM 替换串里写成了 `\$R^2 = 0.949\$`（应为 `$R^2 = 0.949$`）
→ LaTeX 报 `Missing $ inserted`（NC 4 个、Springer 2 个错误）。

**教训重申**：LaTeX 里的 `$` 在 Python 字符串里必须写 `\\$` 或裸 `$`（不转义），
**写成 `\$` 就是在 LaTeX 里输出字面美元号**。

    python tools\_p306_fix_escaped_dollar.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TARGETS = ["paper合/main_nc.tex",
           "paper合/NC_submission/latex_source/main_nc.tex",
           "paper合/main_springer.tex"]

# 把摘要里被写坏的 \$...\$ 还原为 $...$
PAT = re.compile(r"\\\$([^$\\]{1,200}?)\\\$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        # 只改摘要范围内
        m = re.search(r"(\\begin\{abstract\}.*?\\end\{abstract\})", t, re.S) or \
            re.search(r"(\\abstract\{.*?\n\})", t, re.S)
        if not m:
            print(f"  🔴 {Path(rel).name}: 找不到摘要")
            continue
        body = m.group(1)
        n = len(PAT.findall(body))
        fixed = PAT.sub(lambda mm: "$" + mm.group(1) + "$", body)
        left = fixed.count("\\$")
        print(f"  {Path(rel).name}: 修复 {n} 处 \\$…\\$ ｜ 残留 \\$ {left}")
        if n == 0:
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p306")
            if not bak.exists():
                shutil.copy2(p, bak)
            t2 = t[:m.start(1)] + fixed + t[m.end(1):]
            io.open(p, "w", encoding="utf-8", newline="").write(t2)
    if not a.apply:
        print("  （预演）")
        return 0
    print()
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"  复核 {Path(rel).name}: 摘要内 \\$ 残留 = "
              f"{(re.search(r'(begin.abstract.*?end.abstract)', t, re.S) or re.search(r'(abstract..*?\\n.})', t, re.S)).group(1).count(chr(92)+chr(36))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
