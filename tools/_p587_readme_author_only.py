# -*- coding: utf-8 -*-
r"""把 README 的作者行改为**只留姓名**（去掉邮箱与单位）（2026-10-14）。

## 我上一版的问题

`_p586` 先把邮箱替换成占位 `contact@example.com`，**再**替换作者行 ——
顺序反了，导致作者行变成 `**Hongrui Wan** · University of Southampton · \`contact@example.com\``。
**⇒ 占位邮箱仍像联系方式，单位也还在。**

**⇒ 改为只留 `**Hongrui Wan**`**（学术署名；去掉邮箱与单位）。

    python tools\_p587_readme_author_only.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
TARGETS = [PC / "README.md", REPO / "README.md"]

VERSIONS = [
    "**Hongrui Wan** · University of Southampton · `contact@example.com`",
    "**Hongrui Wan** · University of Southampton · `hw4c24@soton.ac.uk`",
    "**Hongrui Wan** · University of Southampton",
]
NEW = "**Hongrui Wan**"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for p in TARGETS:
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        hit = None
        for v in VERSIONS:
            if v in t:
                hit = v
                break
        print(f"  {p.relative_to(REPO)}：命中的旧作者行 = {hit!r}")
        if hit and a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p587")
            if not bak.exists():
                shutil.copy2(p, bak)
            t2 = t.replace(hit, NEW)
            io.open(p, "w", encoding="utf-8", newline="").write(t2)
            print(f"     ✅ 已改为 {NEW!r}")
    if not a.apply:
        print("  （预演）")
        return 0
    print()
    print("  复核：")
    for p in TARGETS:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for s in ("hw4c24", "soton.ac.uk", "hrbeu", "MoYUYao666", "example.com",
                  "University of Southampton"):
            n = t.count(s)
            if n:
                print(f"     🔴 {p.name}：{s} {n} 处")
        head = [l for l in t.splitlines()[:6] if l.strip()]
        print(f"     {p.name} 头部：{head[2][:90] if len(head) > 2 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
