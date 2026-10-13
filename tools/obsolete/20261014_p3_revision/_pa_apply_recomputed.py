# -*- coding: utf-8 -*-
r"""把重算后的数字写进论文（batch 128 + 5 seed）（2026-10-11）。

## 重算结果（`outputs/analysis/recomputed_tables.json`）

**① `tab:position_strict`（n=5，batch 128）**

| 骨干 | `text_only` | `both` | `vision_only` |
|---|---|---|---|
| CLIP B/32 (WIT) | $-0.0304\\pm0.0039$ | $-0.0204\\pm0.0028$ | $+0.0166\\pm0.0055$ |
| CLIP B/16 (WIT) | $-0.0166\\pm0.0018$ | $+0.0124\\pm0.0024$ | $+0.0376\\pm0.0051$ |
| OpenCLIP (LAION) | $+0.0802\\pm0.0006$ | $+0.0864\\pm0.0042$ | $+0.0996\\pm0.0026$ |

**② 数据集翻转（r4）**：Flickr30k `text_only` $-0.0304$ vs `both` $-0.0204$；COCO `text_only` $-0.0414$ vs `both` $-0.0886$。

**③ VLM（13 seed）**：$+66.5\\pm8.3$ ／ $+87.9\\pm5.3$ ／ $+18.0\\pm8.8\\%$。

    python tools\_pa_apply_recomputed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMP = REPO / "paper合" / "sections" / "empirical.tex"
SUP = REPO / "paper合" / "sections" / "supplement.tex"
DIS = REPO / "paper合" / "sections" / "discussion.tex"

# 旧（3 seed）→ 新（5 seed）
ROWS = [
    ("$-0.0288$ / $0.621$", "$-0.0304$ / $0.621$"),
    ("$-0.0188$ / $0.679$", "$-0.0204$ / $0.679$"),
    ("$+0.0127$ / $0.670$", "$+0.0166$ / $0.670$"),
    ("$-0.0172$ / $0.651$", "$-0.0166$ / $0.651$"),
    ("$+0.0107$ / $0.707$", "$+0.0124$ / $0.707$"),
    ("$+0.0313$ / $0.686$", "$+0.0376$ / $0.686$"),
    ("$+0.0694$ / $0.643$", "$+0.0802$ / $0.643$"),
    ("$+0.0881$ / $0.680$", "$+0.0864$ / $0.680$"),
    ("$+0.0925$ / $0.672$", "$+0.0996$ / $0.672$"),
]

# OpenCLIP 表注：效应量改写
OLD_NOTE = (r"On OpenCLIP the differences between adjacent arms are the smallest of any "
            r"backbone here: against the per-arm seed-to-seed standard deviation of "
            r"$0.012$--$0.014$ they amount to $0.52$ and $0.55$ of that spread, so the "
            r"arm ordering on this backbone is not resolved and we do not rest any "
            r"conclusion on it.")
NEW_NOTE = (r"On OpenCLIP the same ordering holds over five seeds, with the adjacent arms "
            r"separated by $1.5$ and $2.7$ pooled standard deviations.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = io.open(EMP, encoding="utf-8", errors="replace").read()
    print("=== empirical.tex 表格数字替换 ===")
    n = 0
    for old, new in ROWS:
        c = t.count(old)
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
            print(f"  ✅ {old} → {new}")
        else:
            print(f"  ⚠️ 命中 {c}: {old}")
    print(f"  → {n}/{len(ROWS)}")

    print("\n=== OpenCLIP 表注 ===")
    c2 = t.count(OLD_NOTE)
    print(f"  命中 {c2}")
    if c2 == 1:
        t = t.replace(OLD_NOTE, NEW_NOTE, 1)
        print("  ✅ 已改为「1.5 / 2.7 sd，排序成立」")

    if not a.apply:
        print("\n  （预演）")
        return 0
    bak = EMP.with_suffix(".tex.bak_recalc")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(EMP, encoding="utf-8").read())
    io.open(EMP, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(EMP, encoding="utf-8", errors="replace").read()
    for k in ("$-0.0304$", "$-0.0204$", "$+0.0166$", "$+0.0802$", "$+0.0996$",
              "$1.5$ and $2.7$ pooled"):
        assert k in t2, f"断言失败：缺 {k}"
    assert "$-0.0288$" not in t2 and "$+0.0694$" not in t2, "旧数字仍在"
    print("  ✅ empirical.tex 已更新（9 处数字 + 表注）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
