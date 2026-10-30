# -*- coding: utf-8 -*-
r"""精查 5 份 Guide 的**决定字段**，每项打印原文与出处（2026-10-07）。

**只查会改变投稿动作的字段**：

| 字段 | 为何关键 |
|---|---|
| **匿名方式**（单盲/双盲） | 双盲要拆题名页 + 匿名稿 → **多一道工** |
| **Article types** | 有无 Research/Full-length 类别 |
| **篇幅规定** | 49 页能否投 |
| **Highlights** | 强制 or 鼓励 |
| **Graphical abstract** | 是否强制 |
| **Data statement 选项** | Option A/B/C，影响仓库开放要求 |

    python tools\_venue_guide_deep.py [KBS|ESWA|IVC|CVIU|IF|all]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
G = REPO / "期刊指南"

J = {
    "KBS":  ("Knowledge-Based Systems", "0950-7051", "_guide_kbs.txt"),
    "ESWA": ("Expert Systems with Applications", "0957-4174", "_guide_eswa.txt"),
    "IVC":  ("Image and Vision Computing", "0262-8856", "_guide_ivc.txt"),
    "CVIU": ("Computer Vision and Image Understanding", "1077-3142", "_guide_cviu.txt"),
    "IF":   ("Information Fusion", "1566-2535", "_guide_infofusion.txt"),
}

QUERIES = [
    ("匿名方式", [r"This journal follows a[n]? \w+ anonymi[sz]ed review process",
                  r"double anonymi[sz]ed peer review"]),
    ("Article types 段", [r"Article types\s+[A-Z]"]),
    ("篇幅/pages 相关句", [r"[^.]{0,160}\bpages?\b[^.]{0,160}\.",
                           r"[^.]{0,140}length[^.]{0,140}\."]),
    ("Highlights 要求句", [r"Highlights[^.]{0,220}\."]),
    ("Graphical abstract", [r"[Gg]raphical abstract[^.]{0,200}\."]),
    ("Data statement 选项", [r"Option [ABC][^.]{0,300}\."]),
    ("摘要句", [r"abstract which does not exceed \d+ words"]),
    ("关键词句", [r"\d+ to \d+ keywords"]),
]


def seg(t, pat, n=1, span=240):
    out = []
    for m in list(re.finditer(pat, t, re.I | re.S))[:n]:
        s = re.sub(r"\s+", " ", m.group(0)).strip()
        out.append(s[:span])
    return out


def main() -> int:
    want = (sys.argv[1] if len(sys.argv) > 1 else "all").upper()
    for k, (name, issn, fn) in J.items():
        if want != "ALL" and want != k:
            continue
        t = io.open(G / fn, encoding="utf-8", errors="ignore").read()
        print("=" * 96)
        print(f"  【{k}】{name}  ISSN {issn}")
        print("=" * 96)
        for label, pats in QUERIES:
            found = []
            for p in pats:
                found += seg(t, p, n=1)
            if not found:
                print(f"  {label:<22} —— **Guide 未提及**")
                continue
            for s in found[:2]:
                print(f"  {label:<22} {s[:210]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
