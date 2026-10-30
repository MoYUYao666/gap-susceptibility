# -*- coding: utf-8 -*-
r"""修字母序（`Anon.` 置顶 + 去 LaTeX 转义后排序）（2026-10-10）。

## 实测错位

```
错位: Huh > Anon.        ← 无作者条应排最前
错位: Wang > Wan         ← "Wan" < "Wang"，但文件里顺序反了
错位: Yi > Y\"uksekg\"on\"ul  ← 排序键含 LaTeX 转义 `\"`
```

**修法**：按**规范化后的姓氏**重排整个书目块（`Anon.` 强制最前）。

    python tools\_p130_fix_order.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"


def sort_key(label: str) -> str:
    fam = label.split(",")[0].strip()
    if fam.startswith("Anon"):
        return "0000"                       # 无作者 → 置顶
    # 去 LaTeX 转义（\"u → u）再规范化
    fam = re.sub(r"\\[a-zA-Z]+\{?([a-zA-Z])\}?", r"\1", fam)
    fam = re.sub(r"\\[^a-zA-Z]", "", fam)
    fam = "".join(c for c in unicodedata.normalize("NFKD", fam)
                  if not unicodedata.combining(c))
    return fam.lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    assert i > 0 and j > i

    head = t[:i]
    block = t[i:j]
    tail = t[j:]

    # 拆出每条 bibitem（含其后的续行，直到下一个 \bibitem）
    m0 = re.search(r"\\begin\{thebibliography\}\{[^}]*\}", block)
    preamble = block[:m0.end()] if m0 else ""
    body = block[m0.end():] if m0 else block
    parts = re.split(r"(?=\\bibitem)", body)
    parts = [p for p in parts if p.strip()]
    print(f"=== 拆出 {len(parts)} 条 ===")

    def label_of(p: str) -> str:
        m = re.search(r"\\bibitem\[([^\]]*)\]", p)
        return m.group(1) if m else "?,"

    before = [label_of(p).split(",")[0] for p in parts]
    parts.sort(key=lambda p: sort_key(label_of(p)))
    after = [label_of(p).split(",")[0] for p in parts]

    n_changed = sum(1 for x, y in zip(before, after) if x != y)
    print(f"  排序后位置变化: {n_changed} 条")
    print("  新顺序前 10:", ", ".join(after[:10]))
    print("  含 Anon. 的位置:",
          [k for k, x in enumerate(after) if x.startswith("Anon")])

    # 校验
    keys = [sort_key(lb) for lb in (label_of(p) for p in parts)]
    ok = all(keys[k] <= keys[k + 1] for k in range(len(keys) - 1))
    print(f"  字母序正确: {'✅' if ok else '❌'}")
    if not ok:
        for k in range(len(keys) - 1):
            if keys[k] > keys[k + 1]:
                print(f"    错位: {after[k]} > {after[k+1]}")

    newblock = preamble + "\n" + "\n".join(p.rstrip() for p in parts)
    t2 = head + newblock + tail

    if not a.apply:
        print("\n  （预演）")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t2)
    print(f"\n  ✅ 已写 {MAIN.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
