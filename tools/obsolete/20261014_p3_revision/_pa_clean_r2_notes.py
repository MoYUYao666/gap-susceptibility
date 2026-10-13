# -*- coding: utf-8 -*-
r"""清除 validation.tex 中剩余两处"is reported separately below"括注（2026-10-02）。

前一轮只改到部分出现位置，仍有两处旧括注残留（L39 附近、L105 附近）。
本脚本按**片段**而非整句匹配，避免转义问题。

    python tools\_pa_clean_r2_notes.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

NOTE = " (the full-fine-tuning pilot is lower, at $0.922$, and is reported separately below)"
REPL = " (the full-fine-tuning pilot fits at $0.922$, and we return to it below)"

NOTE2 = " (the full-fine-tuning pilot is lower, at $0.922$, and is reported separately below) on both CLIP datasets."
REPL2 = " on both CLIP datasets."


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    before = len(re.findall(r"is reported separately below", t))
    print(f"  改前含旧括注: {before} 处")
    # 先清 L105 那种"括注 + 句尾地点短语"的形态，再清剩余括注
    t = t.replace(NOTE2, REPL2)
    t = t.replace(NOTE, REPL)
    after = len(re.findall(r"is reported separately below", t))
    print(f"  改后: {after} 处")
    if after:
        for m in re.finditer(r"[^.]{0,80}is reported separately below[^.]{0,80}\.", t):
            print("   残留: …" + m.group(0).strip()[:180] + "…")
    if apply and after == 0:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "is reported separately below" not in t2
        assert t2.count("we return to it below") >= 1
        print("  ✅ 已写出，无残留")
    elif apply:
        print("  ⚠ 未写回（仍有残留）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
