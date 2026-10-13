# -*- coding: utf-8 -*-
r"""重写 A1 highlights（3 条需改：2 条超 85 字符，1 条与结论冲突）（2026-10-12）。

| # | 旧 | 问题 |
|---|---|---|
| 2 | "Order preservation … but does not improve the stopping decision" | **119 字符**（限 85） |
| 3 | "The bias-field closed form is an identity: …" | **152 字符** |
| 5 | "Tau is a zero-overhead training-time health signal" | **与 E-B 冲突**（决策无优势） |

    python tools\_p233_fix_highlights.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "highlights.tex"

REPL = {
    "Order preservation (Kendall tau) governs zero-shot robustness":
        "Order preservation tracks zero-shot accuracy within a dataset",
    ("Order preservation (Kendall tau) tracks zero-shot accuracy within a dataset, "
     "but does not improve the stopping decision"):
        "Order preservation tracks accuracy within a dataset",
    ("The bias-field closed form is an identity: it reproduces the measured shift to three "
     "decimals as a self-consistency check, not as independent validation"):
        "The bias-field closed form is an identity, not independent validation",
    "Tau is a zero-overhead training-time health signal":
        "Tau costs no extra forward pass, but does not improve stopping",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = 0
    for old, new in REPL.items():
        if old in t:
            print(f"  ✅ 替换 {len(old)} → {len(new)} 字符: {new}")
            t = t.replace(old, new)
            n += 1
    if n == 0:
        print("  ⚠️ 无匹配（可能已改）")

    # 校验长度
    items = []
    for ln in t.splitlines():
        s = ln.strip()
        if s.startswith(r"\item"):
            body = re.sub(r"\\[a-zA-Z]+", "", s[len(r"\item"):]).strip()
            items.append((len(body), body))
    print()
    for L, b in items:
        print(f"  {'✅' if L <= 85 else '🔴'} [{L:3}] {b}")
    over = [b for L, b in items if L > 85]
    if over:
        print(f"\n  🔴 仍有 {len(over)} 条超限")
        return 1
    if len(items) < 3 or len(items) > 5:
        print(f"\n  🔴 条数 {len(items)} 不在 3–5")
        return 1
    if not args.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p233")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print(f"\n  ✅ highlights 已改（{len(items)} 条，最长 {max(L for L, _ in items)} 字符）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
