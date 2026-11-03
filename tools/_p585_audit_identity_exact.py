# -*- coding: utf-8 -*-
r"""精确核验：发布库里属于作者本人的身份信息（2026-10-14）。

## 要区分的两类

| 类 | 例 | 处置 |
|---|---|---|
| **作者本人信息** | `hw4c24@soton.ac.uk`、`2024282101@hrbeu.edu.cn`、GitHub 用户名 | **清掉** |
| **外部数据** | 数据集页脚、第三方论文作者邮箱、指南文本 | **保留**（那是数据，不是个人信息） |

**⇒ 只按"确定属于作者"的字面串搜索**，不做宽泛正则（避免误报与误删）。

    python tools\_p585_audit_identity_exact.py
"""
from __future__ import annotations

import collections
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

OWN = [
    ("hw4c24@soton.ac.uk", "作者邮箱（Southampton 校园账号）"),
    ("2024282101@hrbeu.edu.cn", "作者邮箱（提交身份）"),
    ("hw4c24", "校园账号片段"),
    ("MoYUYao666", "GitHub 用户名"),
    ("0009-0003-8649-7504", "ORCID"),
]

# 只有这些位置**需要**清（数据文件里的第三方邮箱不动）
CLEAN_hint = ("README.md", "tools/", "requirements.txt", ".gitignore")


def main() -> int:
    print("=" * 100)
    print("① 作者本人信息的**精确**出现位置")
    print("=" * 100)
    files = [p for p in PC.rglob("*") if p.is_file() and ".git" not in p.parts]
    per = collections.defaultdict(list)
    for p in files:
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        for s, label in OWN:
            n = t.count(s)
            if n:
                per[label].append((p.relative_to(PC).as_posix(), n))
    for _, label in OWN:
        hits = per.get(label, [])
        tot = sum(n for _, n in hits)
        print(f"  ── {label}：{tot} 处，分布在 {len(hits)} 个文件")
        for f, n in sorted(hits, key=lambda x: -x[1])[:12]:
            print(f"       {n:>4}×  {f}")

    print()
    print("=" * 100)
    print("② 其中**该清**的（README / tools / 根文件）")
    print("=" * 100)
    todo = []
    for _, label in OWN:
        for f, n in per.get(label, []):
            if any(f.startswith(h) or f == h.rstrip("/") for h in CLEAN_hint):
                todo.append((f, label, n))
    agg = collections.Counter()
    for f, label, n in todo:
        agg[(f, label)] += n
    for (f, label), n in sorted(agg.items(), key=lambda kv: -kv[1]):
        print(f"     {n:>4}×  {label:<28} {f}")
    print(f"  ⇒ 需清理 {len(agg)} 个（文件, 信息类）组合")

    print()
    print("=" * 100)
    print("③ **数据文件**里出现的（不动）")
    print("=" * 100)
    keep = [(f, label, n) for f, label, n in todo if not any(
        f.startswith(h) or f == h.rstrip("/") for h in CLEAN_hint)]
    kept_other = 0
    for _, label in OWN:
        for f, n in per.get(label, []):
            if not any(f.startswith(h) or f == h.rstrip("/") for h in CLEAN_hint):
                kept_other += 1
                print(f"     {n:>4}×  {label:<28} {f}")
    print(f"  ⇒ 保留 {kept_other} 个（属数据/历史产物）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
