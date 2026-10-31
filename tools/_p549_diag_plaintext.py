# -*- coding: utf-8 -*-
r"""逐步诊断 `_p548` 的膨胀点（2026-10-13）。

    python tools\_p549_diag_plaintext.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
REPO = Path(__file__).resolve().parents[1]
OUTDIR = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"

import importlib.util
spec = importlib.util.spec_from_file_location("m", REPO / "tools" / "_p548_plaintext_responses.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def main() -> int:
    src = OUTDIR / "P3_RESPONSE_Reviewer1.txt"
    t = io.open(src, encoding="utf-8", errors="replace").read()
    print(f"  源 {len(t):,} 字符")
    print()

    steps = []
    a = t.replace("**Response:** **Response.** ", "**Response:** ")
    a = a.replace("**Response:** **Response.**", "**Response:**")
    steps.append(("0 去重复标签", a))

    def math(m):
        s = m.group(1)
        for pat, rep in M.SYMS:
            s = re.sub(pat, rep, s)
        s = s.replace("\\", "").replace("{", "").replace("}", "")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    b = re.sub(r"\$([^$]*)\$", math, a)
    steps.append(("1 $..$ 替换", b))

    c = b
    for pat, rep in M.SYMS:
        c = re.sub(pat, rep, c)
    steps.append(("2 剩余 SYMS", c))

    d = re.sub(r"\*\*([^*]+)\*\*", r"\1", c)
    steps.append(("3 粗体", d))
    e = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", d)
    steps.append(("4 斜体", e))
    f = re.sub(r"`([^`]*)`", r"\1", e)
    steps.append(("5 反引号", f))
    g = f.replace("\\", "")
    steps.append(("6 去反斜杠", g))

    prev = len(t)
    for name, s in steps:
        delta = len(s) - prev
        flag = "🔴" if abs(delta) > 2000 else "  "
        print(f"  {flag} {name:<16} {len(s):>8,} 字符  (Δ{delta:+,})")
        prev = len(s)
    print()
    print(f"  ⇒ 膨胀 {len(g) - len(t):+,} 字符")
    if len(g) > len(t) * 2:
        print("  ⇒ 找出最大膨胀步骤并看它改了什么：")
        for i, (name, s) in enumerate(steps):
            if i and len(s) > len(steps[i - 1][1]) * 1.5:
                before = steps[i - 1][1]
                print(f"     在「{name}」膨胀。采样前 300 字符的差异：")
                print(f"       之前：{before[:300]!r}")
                print(f"       之后：{s[:300]!r}")
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
