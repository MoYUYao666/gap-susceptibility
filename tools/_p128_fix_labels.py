# -*- coding: utf-8 -*-
r"""修 `[?]` 嵌套方括号 + 年份不一致（2026-10-10）。

## 三个问题（实测）

| 问题 | 现象 | 修法 |
|---|---|---|
| **嵌套方括号** | `\bibitem[[?], 2026]{imod}` → LaTeX 在第一个 `]` 处闭合 → **该条被吞** | 标签改 `Anon., 2026`；正文的 `[...]` 去掉 |
| **年份不一致** | `yuksekgonul2023when` 标 `2022`（OpenAlex），bibitem 写 **ICLR 2023** | **以 bibitem 的年份为准** |
| **`under review` 不像 APA** | `wan2026protect` = "under review, Pattern Recognition, 2026" | 改为 `Manuscript under review.` |

    python tools\_p128_fix_labels.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"
FIXED = REPO / "outputs" / "analysis" / "a1_apa_fixed.json"

# bibitem 里写明的年份（优先于 OpenAlex）
YEAR_FROM_BIB = {"yuksekgonul2023when": "2023", "levi2025": "2025"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()

    n_label = n_year = n_review = 0

    # ① 无作者条的标签 `[[?], YYYY]` → `[Anon., YYYY]`，并去掉正文的方括号
    def fix_anon(m):
        nonlocal n_label
        n_label += 1
        year = m.group(1)
        key = m.group(2)
        rest = m.group(3)
        rest = re.sub(r"^\s*\[(.*?)\]\s*", r"\1 ", rest)     # 去正文方括号
        rest = re.sub(r"\s*%\s*[^\n]*", "", rest)             # 去注释
        return f"\\bibitem[Anon., {year}]{{{key}}} {rest.strip()}"
    t2 = re.sub(r"\\bibitem\[\[\?\], (\d{4})\]\{([^}]*)\}([^\n]*)", fix_anon, t)
    t = t2

    # ② 年份以 bibitem 为准
    for key, yr in YEAR_FROM_BIB.items():
        pat = re.compile(r"(\\bibitem\[[^\]]*?, )(\d{4})(\]\{" + re.escape(key) + r"\})")
        t2, n = pat.subn(lambda m: m.group(1) + yr + m.group(3), t)
        if n:
            n_year += n
            t = t2

    # ③ under review → APA 写法
    t2, n = re.subn(r"\. under review, Pattern Recognition, 2026\.",
                    ". Manuscript under review.", t)
    n_review += n
    t = t2
    t2, n = re.subn(r"under review, [A-Za-z ]+, \d{4}\.", "Manuscript under review.", t)
    n_review += n
    t = t2

    print("=== 改动 ===")
    print(f"  `[[?], YYYY]` → `[Anon., YYYY]` 并去方括号: {n_label} 处")
    print(f"  年份按 bibitem 修正: {n_year} 处")
    print(f"  under review → Manuscript under review: {n_review} 处")
    print(f"  现存 `[[?]` 残留: {t.count('[[?]')}")

    if not a.apply:
        print("\n  （预演）")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print(f"\n  ✅ 已写 {MAIN.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
