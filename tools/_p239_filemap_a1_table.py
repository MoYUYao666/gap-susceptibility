# -*- coding: utf-8 -*-
r"""更新 `文件地图.md` 里 A1 状态表的两行（L113-114）（2026-10-12）。

    python tools\_p239_filemap_a1_table.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "文件地图.md"

PAIRS = [
    ("> | 编译 | **41 页 / 0 错误 / 0 未定义引用 / 0 Overfull** |",
     "> | 编译 | **42 页 / 0 错误 / 0 未定义引用 / 0 Warning** |"),
    ("> | 标题 | *Order Preservation as a Zero-Overhead Monitor for Classification "
     "Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric* |",
     "> | 标题 | *Order Preservation Tracks Zero-Shot Accuracy under Classification "
     "Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric* "
     "（**2026-10-12 改**：原 *…as a Zero-Overhead Monitor…*） |"),
    ("> | 摘要 | **245 词**（NN 限 250）｜关键词 **5**｜highlights **5 条** |",
     "> | 摘要 | **249 词**（NN 限 250）｜关键词 **5**｜highlights **5 条**（最长 69 字符） |"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = 0
    for i, (o, w) in enumerate(PAIRS):
        c = t.count(o)
        print(f"  {'✅' if c == 1 else '🔴'} 锚点#{i + 1}: 命中 {c}")
        if c == 1:
            t = t.replace(o, w, 1)
            n += 1
    if n != len(PAIRS):
        print("  🔴 有未命中，不写入")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".md.bak_p239")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = ("Tracks Zero-Shot Accuracy under Classification" in t2
          and "**42 页 / 0 错误" in t2 and "249 词" in t2)
    print(f"  {'✅ 已更新' if ok else '🔴 失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
