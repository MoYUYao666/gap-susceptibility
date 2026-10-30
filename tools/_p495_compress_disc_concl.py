# -*- coding: utf-8 -*-
r"""压缩 discussion 与 conclusion（2026-10-13）。

## 依据（`tools/_p491`）

| 节 | 散文字符 | 可压点 |
|---|---|---|
| **discussion** | **5,021**（100% 散文） | **12 条 limitation 表格化**；Future Directions 压缩 |
| **conclusion** | **2,700**（100% 散文） | 压为 1 段 |

**⇒ 两节合计 7,721 字符（≈0.9 页），目标压掉 ~50%。**

**⚠️ 纪律**：`discussion.tex` 里的 **Eleventh limitation（Adapter `up.bias`）**、
**Twelfth limitation（画廊抽样噪声）**、**"both vs vision_only 未决"** 都是本轮新增的关键限定，
**必须保留**（可压措辞，不可删结论）。

    python tools\_p495_compress_disc_concl.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
DI = PI / "sections" / "discussion.tex"
CO = PI / "sections" / "conclusion.tex"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for p in (DI, CO):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        # 统计 limitation 条数
        n_lim = len(re.findall(r"\\textbf\{[^}]*[Ll]imitation|\bLimitation\b", t))
        print(f"  {p.name}: {len(t):,} 字符 ｜ 含 limitation 关键词 {n_lim} 处")
    print()
    print("  计划：")
    print("    discussion → 保留全部 limitation 的**结论句**，把展开说明压成一句；")
    print("                 Future Directions 压为 2 句；Alignment-in-context 段压 1/3")
    print("    conclusion → 压为 1 段（≤120 词）")
    if not a.apply:
        print("  （预演）")
        return 0
    print("  ⚠️ 本节压缩需**逐段人工判断**（哪些句子是结论、哪些是展开），")
    print("     不适合纯正则替换 ⇒ 请用 edit 工具逐段改，或由成员按 reviewer 视角重写。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
