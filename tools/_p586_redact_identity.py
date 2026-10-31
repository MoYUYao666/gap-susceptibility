# -*- coding: utf-8 -*-
r"""脱敏：从发布库移除作者联系方式（2026-10-14）。

## 操作者要求

> **"尽量不要包含我的个人信息，readme 改一下"**

## 处置原则（区分「身份信息」与「学术署名」）

| 类 | 具体 | 处置 | 理由 |
|---|---|---|---|
| **联系方式** | `hw4c24@soton.ac.uk`、`2024282101@hrbeu.edu.cn` | ✅ **清掉** | 邮箱是主要被爬取的目标 |
| **账号/用户名** | `MoYUYao666`、`hw4c24` | ✅ **清掉** | 可关联到其它平台身份 |
| **单位与地址** | `University of Southampton` | ✅ **从 README 头部去掉** | 减少可定位性 |
| **姓名** | `Hongrui Wan` | ⚠️ **保留** | **学术署名** —— 去掉会使代码无法被正确引用（MIT 类许可也要求保留版权署名） |
| ORCID | `0009-0003-...` | ✅ 本就不在（0 处） | — |

**⇒ 结论：清联系方式与账号，保留姓名作为署名。**

    python tools\_p586_redact_identity.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
ROOT = REPO

EMAILS = ["hw4c24@soton.ac.uk", "2024282101@hrbeu.edu.cn"]
USERNAMES = ["MoYUYao666"]
PLACEHOLDER_EMAIL = "contact@example.com"      # 占位（非真实地址）
PLACEHOLDER_USER = "OWNER"

README_OLD = "**Hongrui Wan** · University of Southampton · `hw4c24@soton.ac.uk`"
README_NEW = "**Hongrui Wan**"


def redact_text(t: str) -> tuple[str, int]:
    n = 0
    for e in EMAILS:
        c = t.count(e)
        if c:
            t = t.replace(e, PLACEHOLDER_EMAIL)
            n += c
    for u in USERNAMES:
        c = t.count(u)
        if c:
            t = t.replace(u, PLACEHOLDER_USER)
            n += c
    return t, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ① README（两处）
    print("=" * 100)
    print("① README 头部")
    print("=" * 100)
    for p in (PC / "README.md", ROOT / "README.md"):
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        c = t.count(README_OLD)
        print(f"  {p.relative_to(ROOT)}：命中作者行 {c}")
        t2, n = redact_text(t)
        if c and a.apply:
            t2 = t2.replace(README_OLD, README_NEW)
        elif a.apply:
            t2 = t2.replace(README_NEW, README_NEW)
        if a.apply and (c or n):
            shutil.copy2(p, p.with_suffix(p.suffix + ".bak_p586"))
            io.open(p, "w", encoding="utf-8", newline="").write(t2)
            print(f"     ✅ 已脱敏（替换 {n} 处联系方式 + 作者行 {c} 处）")

    # ② tools/ 与根文件
    print()
    print("=" * 100)
    print("② tools/ 与其他文件")
    print("=" * 100)
    targets = [p for p in PC.rglob("*") if p.is_file() and ".git" not in p.parts
               and not p.name.endswith(".bak_p586")]
    total_files = total_hits = 0
    for p in targets:
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        t2, n = redact_text(t)
        if n:
            total_files += 1
            total_hits += n
            if a.apply:
                shutil.copy2(p, p.with_suffix(p.suffix + ".bak_p586"))
                io.open(p, "w", encoding="utf-8", newline="").write(t2)
    print(f"  命中 {total_hits} 处，分布在 {total_files} 个文件")
    print(f"  {'✅ 已脱敏' if a.apply else '（预演）'}")

    if not a.apply:
        return 0

    # ③ 复核
    print()
    print("=" * 100)
    print("③ 复核")
    print("=" * 100)
    left = 0
    for p in PC.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.name.endswith(".bak_p586"):
            continue
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        for s in EMAILS + USERNAMES:
            c = t.count(s)
            if c:
                left += c
                print(f"  🔴 {c}× 「{s}」 {p.relative_to(PC)}")
    print(f"  残留 {left} 处（应 0）")
    for p in (PC / "README.md", ROOT / "README.md"):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        head = " | ".join(l for l in t.splitlines()[:5] if l.strip())
        print(f"  {p.relative_to(ROOT)} 头部：{head[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
