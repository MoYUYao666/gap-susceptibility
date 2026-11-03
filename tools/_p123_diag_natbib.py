# -*- coding: utf-8 -*-
r"""查 natbib 冲突的真因 + 修 `&` 未转义（2026-10-10）。

    python tools\_p123_diag_natbib.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"


def main() -> int:
    log = io.open(A1 / "main.log", encoding="utf-8", errors="replace").read()
    i = log.find("Option clash for package natbib")
    print("=== 冲突处日志（前后 900 字符）===")
    if i > 0:
        print(log[max(0, i - 500):i + 400])
    else:
        print("  （未找到）")

    print("\n=== 日志中所有 natbib 相关行 ===")
    for ln in log.splitlines():
        if "natbib" in ln.lower() or "citation" in ln.lower():
            print("  " + ln.strip()[:130])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
