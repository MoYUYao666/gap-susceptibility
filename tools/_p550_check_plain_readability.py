# -*- coding: utf-8 -*-
r"""抽查三份纯文本回复的可读性（2026-10-13）。

    python tools\_p550_check_plain_readability.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTDIR = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"


def main() -> int:
    for p in sorted(OUTDIR.glob("*_plain.txt")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print("=" * 96)
        print(f"{p.name}（{len(t):,} 字符）")
        print("=" * 96)
        print("\n".join("  " + l for l in t.splitlines()[:14]))
        print("  …")
        # 检查是否有可疑残留
        print()
        print("  检查：")
        for pat, label in ((r"\\[a-zA-Z]+", "LaTeX 命令"), (r"\$\d", "裸 $"),
                           (r"\*\*", "** 标记"), (r"\\times|\bGamma\b|\bnabla\b", "可读化了的符号（期望有）")):
            n = len(re.findall(pat, t))
            flag = "✅" if (n == 0) == ("期望有" not in label) else "⚠️"
            print(f"    {flag} {label}: {n} 处")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
