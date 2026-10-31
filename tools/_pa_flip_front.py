# -*- coding: utf-8 -*-
r"""补:翻转段前半句的 3-seed 数字 → 5-seed（2026-10-11）。

`validation.tex` 里：
> *"text-only holds the gap at $-0.0288\pm0.0013$ on Flickr30k against $-0.0188\pm0.0004$ for the
> both-position arm, whereas on MS-COCO the ordering is the reverse: text-only gives $-0.0414\pm0.0015$
> and both-position $-0.0886\pm0.0026$"*

**5-seed 实测**（batch 128）：
Flickr30k `text_only` $-0.0304\pm0.0039$｜`both` $-0.0204\pm0.0028$
COCO `text_only` $-0.0414\pm0.0015$｜`both` $-0.0886\pm0.0026$（COCO 侧未变，本就是 128）

    python tools\_pa_flip_front.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

OLD = (r"text-only holds the gap at $-0.0288\pm0.0013$ on Flickr30k against $-0.0188\pm0.0004$ for the "
       r"both-position arm")
NEW = (r"text-only holds the gap at $-0.0304\pm0.0039$ on Flickr30k against $-0.0204\pm0.0028$ for the "
       r"both-position arm")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
    if n != 1:
        return 1
    t2 = t.replace(OLD, NEW, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in (r"$-0.0304\pm0.0039$", r"$-0.0204\pm0.0028$"):
        assert k in t3, f"断言失败：缺 {k}"
    assert "-0.0288" not in t3 and "-0.0188" not in t3, "旧数字仍在"
    print("  ✅ 已更新为 5-seed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
