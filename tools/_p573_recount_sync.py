# -*- coding: utf-8 -*-
r"""按「只推代码 + 结果 JSON」的方案重算同步集（2026-10-14）。

## 排除规则（操作者选定）

| 排除 | 判据 |
|---|---|
| 模型权重 | `.pt .pth .bin .safetensors .ckpt .onnx .h5 .pkl .npz .npy .parquet .db .sqlite` |
| 压缩包 | `.zip .tar .gz .7z .rar` |
| 音视频 | `.mp4 .avi .mov .wav .mp3` |
| 日志 | `.log` |
| 稿件类 | `main*` / `cover_letter*` / `title_page*` / `highlights*` / `*.docx` |
| **一次性脚本** | `tools/_*`（**1171 个**）⇒ 移入 `tools/obsolete/` 而非直接排除（**保留可追溯**） |
| 云端目录快照 | `outputs/_cloud_layout`（1001 个） |

**⚠️ 另有约束**：**单文件 <100 MB**（GitHub 硬限；超限需 LFS）。

    python tools\_p573_recount_sync.py
"""
from __future__ import annotations

import collections
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

EXCLUDE_EXT = {".pt", ".pth", ".bin", ".safetensors", ".ckpt", ".onnx", ".h5", ".pkl",
               ".npz", ".npy", ".parquet", ".db", ".sqlite", ".zip", ".tar", ".gz",
               ".7z", ".rar", ".mp4", ".avi", ".mov", ".wav", ".mp3", ".log",
               ".docx", ".doc", ".bak"}
BAN_NAME = re.compile(r"(^|/)(main[^/]*\.(tex|pdf)|cover_letter[^/]*|title_page[^/]*|"
                      r"highlights[^/]*|.*\.bak.*$)", re.I)
SKIP_DIRS = {"outputs/_cloud_layout"}


def keep(p: Path) -> bool:
    rel = p.relative_to(REPO).as_posix()
    if p.suffix.lower() in EXCLUDE_EXT:
        return False
    if BAN_NAME.search(rel):
        return False
    for d in SKIP_DIRS:
        if rel.startswith(d + "/") or rel == d:
            return False
    return True


def main() -> int:
    print("=" * 100)
    print("① 按方案 1 重算：保留代码 + 结果 JSON（<100 MB）")
    print("=" * 100)
    stats = collections.Counter()
    sizes = collections.Counter()
    big = []
    per_top = collections.Counter()
    per_top_sz = collections.Counter()
    for top in ("tools", "outputs", "src", "exp", "experiments", "docs"):
        src = REPO / top
        if not src.is_dir():
            continue
        for p in src.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(REPO)
            dst = PC / rel
            if dst.exists() and p.stat().st_mtime <= dst.stat().st_mtime + 1:
                continue
            if not keep(p):
                stats["排除"] += 1
                continue
            sz = p.stat().st_size
            if sz > 100 * 1024 * 1024:
                stats["超 100 MB（须排除）"] += 1
                big.append((sz, rel.as_posix()))
                continue
            stats["保留"] += 1
            sizes["合计字节"] += sz
            per_top[top] += 1
            per_top_sz[top] += sz
            if sz > 5 * 1024 * 1024:
                big.append((sz, rel.as_posix()))
    print(f"     排除 {stats['排除']} 个 ｜ 超 100 MB 再排除 {stats['超 100 MB（须排除）']} 个 ｜ "
          f"**保留 {stats['保留']} 个**")
    print(f"     ⇒ 总体积 **{sizes['合计字节']/1024/1024:.1f} MB**")
    print()
    print("  保留的按顶层目录：")
    for t in sorted(per_top, key=lambda x: -per_top[x]):
        print(f"     {t:<14} {per_top[t]:>5} 个 ｜ {per_top_sz[t]/1024/1024:>8.2f} MB")
    print()
    if big:
        print("  ⚠️ 体积最大的 10 个（含 5 MB 以上，需逐一确认是否该推）：")
        for sz, n in sorted(big, reverse=True)[:10]:
            print(f"     {sz/1024/1024:>8.2f} MB  {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
