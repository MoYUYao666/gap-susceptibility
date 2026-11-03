# -*- coding: utf-8 -*-
r"""修 `\logit` 未定义（`\logit` 不是 LaTeX 命令）（2026-10-12）。

编译错误：`! Undefined control sequence. l.46 ...very other row in this paper ($\exp(\logit`

    python tools\_p397_fix_logit_macro.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
E = REPO / "paper合" / "sections" / "empirical.tex"

OLD = r"$\exp(\logit) = 14.29$ against $100$"
NEW = r"$\exp(\mathrm{logit\_scale}) = 14.29$ against $100$"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(E, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        i = t.find("\\logit")
        print("  附近: " + repr(t[max(0, i - 120):i + 120]) if i >= 0 else "  （找不到 \\logit）")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = E.with_suffix(".tex.bak_p397")
    if not bak.exists():
        shutil.copy2(E, bak)
    io.open(E, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    t2 = io.open(E, encoding="utf-8", errors="replace").read()
    print(f"  {'✅ 已修' if '\\logit' not in t2 else '🔴 仍有 \\logit'}")
    return 0 if "\\logit)" not in t2 and "\\logit " not in t2 and "(\\logit" not in t2 else 2


if __name__ == "__main__":
    raise SystemExit(main())
