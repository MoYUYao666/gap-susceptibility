# -*- coding: utf-8 -*-
r"""审查将同步的新增文件：构成、体积、可疑项（2026-10-14）。

    python tools\_p572_audit_sync_candidates.py
"""
from __future__ import annotations

import collections
import io
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

ALLOW_TOP = {"tools", "outputs", "src", "exp", "experiments", "docs"}


def main() -> int:
    print("=" * 100)
    print("① 新增/更新文件的体积分布")
    print("=" * 100)
    buckets = collections.Counter()
    total = 0
    biggest = []
    for top in sorted(ALLOW_TOP):
        src = REPO / top
        if not src.is_dir():
            continue
        for p in src.rglob("*"):
            if not p.is_file():
                continue
            dst = PC / p.relative_to(REPO)
            is_new = not dst.exists()
            is_upd = dst.exists() and p.stat().st_mtime > dst.stat().st_mtime + 1
            if not (is_new or is_upd):
                continue
            sz = p.stat().st_size
            total += sz
            if sz > 10 * 1024 * 1024:
                buckets[" >10 MB"] += 1
            elif sz > 1024 * 1024:
                buckets[" 1-10 MB"] += 1
            elif sz > 100 * 1024:
                buckets[" 100 KB-1 MB"] += 1
            else:
                buckets[" <100 KB"] += 1
            biggest.append((sz, p.relative_to(REPO).as_posix()))
    for k in (" >10 MB", " 1-10 MB", " 100 KB-1 MB", " <100 KB"):
        print(f"     {k:<14} {buckets.get(k, 0):>5} 个")
    print(f"     ⇒ 合计 {sum(buckets.values())} 个 / {total/1024/1024:.1f} MB")
    print()
    print("  最大的 12 个：")
    for sz, name in sorted(biggest, reverse=True)[:12]:
        print(f"     {sz/1024/1024:>8.1f} MB  {name}")

    print()
    print("=" * 100)
    print("② `tools/` 新增脚本：按前置下划线分类（一次性 vs 可重跑管线）")
    print("=" * 100)
    new_tools = []
    for p in (REPO / "tools").rglob("*.py"):
        dst = PC / p.relative_to(REPO)
        if not dst.exists() or p.stat().st_mtime > dst.stat().st_mtime + 1:
            new_tools.append(p.name)
    tmp = [n for n in new_tools if n.startswith("_")]
    pipe = [n for n in new_tools if not n.startswith("_")]
    print(f"     新增 {len(new_tools)} 个：`_` 前缀（一次性/审计）**{len(tmp)}** ｜ 无前缀（管线）**{len(pipe)}**")
    print(f"     无前缀示例：{sorted(pipe)[:12]}")

    print()
    print("=" * 100)
    print("③ `outputs/` 新增：按子目录分类")
    print("=" * 100)
    d = collections.Counter()
    for p in (REPO / "outputs").rglob("*"):
        if not p.is_file():
            continue
        dst = PC / p.relative_to(REPO)
        if not dst.exists() or p.stat().st_mtime > dst.stat().st_mtime + 1:
            rel = p.relative_to(REPO)
            parts = rel.parts
            key = "/".join(parts[:2]) if len(parts) > 2 else "/".join(parts[:1])
            d[key] += 1
    for k, n in d.most_common(18):
        print(f"     {k:<40} {n:>5}")

    print()
    print("=" * 100)
    print("④ 可疑项扫描")
    print("=" * 100)
    SUS = [(r"\.(safetensors|bin|pt|pth|ckpt|onnx|h5|pkl|npz|npy|parquet|db|sqlite)$", "模型/权重/数据库"),
           (r"\.(mp4|avi|mov|wav|mp3)$", "音视频"),
           (r"(^|/)(flickr30k|coco|data|datasets?)/", "数据集目录"),
           (r"\.(zip|tar|gz|7z|rar)$", "压缩包"),
           (r"\.log$", "日志")]
    flagged = 0
    for pat, label in SUS:
        hits = []
        for top in sorted(ALLOW_TOP):
            for p in (REPO / top).rglob("*"):
                if not p.is_file():
                    continue
                rel = p.relative_to(REPO).as_posix()
                if re.search(pat, rel, re.I):
                    dst = PC / p.relative_to(REPO)
                    if not dst.exists() or p.stat().st_mtime > dst.stat().st_mtime + 1:
                        hits.append(rel)
        n = len(hits)
        flagged += n
        flag = "⚠️" if n else "✅"
        print(f"     {flag} {label:<18} {n:>5} 个")
        for h in hits[:3]:
            print(f"          {h}")
    print()
    print(f"  ⇒ 可疑项合计 {flagged} 个（需逐一判断是否该推）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
