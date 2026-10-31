# -*- coding: utf-8 -*-
r"""改表注：`single-seed` → `three-seed means`（精确匹配，含换行）（2026-10-10）。

    python tools\_pa_table_caption.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = ("The $\\dagger$ rows are single-seed\n"
       "runs under the same protocol, whereas the archived rows are five-seed means; on CLIP B/32 "
       "the seed-to-seed\n"
       "standard deviation is $0.003$, so the gaps those single runs separate are several times "
       "that spread.")

NEW = ("The $\\dagger$ rows are three-seed means\n"
       "under the same protocol, as are the archived rows, which use five seeds; on CLIP B/32 "
       "the seed-to-seed\n"
       "standard deviation is $0.001$--$0.002$, so the gaps those arms separate are several times "
       "that spread.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "three-seed means" in t:
        print("  已改，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD)}）")
        return 1
    t = t.replace(OLD, NEW, 1)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "three-seed means" in t2 and "single-seed" not in t2.split("\\caption")[1][:1500]
    print("  ✅ 表注已改：three-seed means（并去掉 single-seed 的说法）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
