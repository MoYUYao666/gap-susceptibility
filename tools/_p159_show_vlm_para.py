# -*- coding: utf-8 -*-
r"""看 `discussion.tex` 里解码器 VLM 那段的确切原文（供改写）（2026-10-10）。

    python tools\_p159_show_vlm_para.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    i = t.find("decay under both the text-only and both-position arms")
    if i < 0:
        i = t.find("tab:vlm")
    if i < 0:
        print("(未找到)")
        return 1
    # 往前到段落起，往后到段落末
    s = t.rfind("\n\n", 0, i)
    e = t.find("\n\n", i)
    print("=" * 74)
    print("段落范围:", s, "→", e)
    print("=" * 74)
    print(repr(t[s:e]))
    print()
    print("=" * 74)
    print("可读版")
    print("=" * 74)
    print(" ".join(t[s:e].split()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
