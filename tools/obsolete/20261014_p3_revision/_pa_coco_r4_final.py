# -*- coding: utf-8 -*-
r"""把 COCO r4 的两臂新值写进论文与台账（2026-10-11 晚）。

## 精确值（`outputs/coco_sweep{,_text_only}/r4/`，n=5，batch 128）

| 臂 | mean | sd |
|---|---|---|
| `text_only` | $-0.043013$ | $0.002777$ |
| `both` | $-0.087733$ | $0.002226$ |

**旧值**：`text_only` $-0.0414\pm0.0015$（3 seed）｜`both` $-0.0886\pm0.0026$（3 seed）

## 顺带

VLM `both` sd：`5.3` → `5.4`（若还有残留）

    python tools\_pa_coco_r4_final.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VAL = REPO / "paper合" / "sections" / "validation.tex"
LED = REPO / "tools" / "_claim_ledger.py"

PAIRS_VAL = [
    (r"text-only gives $-0.0430\pm0.0028$ and both-position $-0.0886\pm0.0026$",
     r"text-only gives $-0.0430\pm0.0028$ and both-position $-0.0877\pm0.0022$"),
]
PAIRS_LED = [
    ('("COCO|both", -0.0886)', '("COCO|both", -0.0877)'),
]
# VLM sd 残留
PAIRS_VLM = [(r"87.9\pm5.3", r"87.9\pm5.4")]


def fix(path: Path, pairs, tag: str) -> int:
    t = io.open(path, encoding="utf-8", errors="replace").read()
    n = 0
    for old, new in pairs:
        c = t.count(old)
        print(f"  [{tag}] {'✅' if c == 1 else '⚠️'} 命中 {c}: {old[:56]}")
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
        elif c > 1:
            t = t.replace(old, new)
            n += c
    if n:
        if not A:
            return n
        io.open(path, "w", encoding="utf-8", newline="").write(t)
    return n


A = False


def main() -> int:
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    A = args.apply

    print("=== validation.tex ===")
    fix(VAL, PAIRS_VAL, "val")
    print("=== 台账 ===")
    fix(LED, PAIRS_LED, "led")
    print("=== VLM both sd 残留（supplement + discussion）===")
    for f in (REPO / "paper合" / "sections" / "supplement.tex",
              REPO / "paper合" / "sections" / "discussion.tex"):
        fix(f, PAIRS_VLM, f.name)

    if not A:
        print("\n  （预演）")
        return 0

    # 断言
    v = io.open(VAL, encoding="utf-8", errors="replace").read()
    assert r"$-0.0877\pm0.0022$" in v, "validation 新值未写入"
    assert r"$-0.0886\pm0.0026$" not in v, "validation 旧值仍在"
    l = io.open(LED, encoding="utf-8").read()
    assert '("COCO|both", -0.0877)' in l, "台账新值未写入"
    try:
        ast.parse(l)
    except SyntaxError as e:
        print(f"  ❌ 台账语法错误: {e}")
        return 1
    for f in (REPO / "paper合" / "sections" / "supplement.tex",
              REPO / "paper合" / "sections" / "discussion.tex"):
        x = io.open(f, encoding="utf-8", errors="replace").read()
        assert "87.9\\pm5.3" not in x, f"{f.name} 仍有 sd 5.3"
    print("\n  ✅ validation + 台账 + VLM sd 全部已更新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
