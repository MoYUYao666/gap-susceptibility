# -*- coding: utf-8 -*-
r"""查 `_p222` 六项的实际落地状态（2026-10-12）。

    python tools\_p226_status.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"


def main() -> int:
    mt = io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read()
    hl = io.open(A1 / "highlights.tex", encoding="utf-8", errors="replace").read()
    ab = io.open(A1 / "abstract.tex", encoding="utf-8", errors="replace").read()
    vd = REPO / "docs" / "A1_VENUE_DECISION.md"
    vt = io.open(vd, encoding="utf-8", errors="replace").read() if vd.exists() else ""

    checks = [
        ("1 标题去掉 Monitor", "Zero-Overhead Monitor" not in mt
         and "Tracks Zero-Shot Accuracy" in mt),
        ("1b abstract.tex 标题同步", "Tracks Zero-Shot Accuracy" in ab
         and "Zero-Overhead Monitor" not in ab),
        ("2 highlights r=1.000 加限定", "self-consistency check" in hl),
        ("3 four decimals → three", "four decimals" not in mt
         and "three decimals" in mt),
        ("4 zero-overhead monitor 句已改", "zero-overhead training-time monitor" not in mt),
        ("4b 摘要 'governs' 已改", "Only the second governs" not in mt),
        ("5 sec:epoch_sweep 新小节", "sec:epoch_sweep" in mt),
        ("5b 组内证据写入", "+0.840" in mt or "0.840" in mt),
        ("5c 决策局限写入", "59.44" in mt),
        ("6 docs 过期更正", "2026-10-12 更正" in vt),
        ("6b abstract.tex 摘要体已同步", "Tracks Zero-Shot Accuracy" in ab),
    ]
    print("=" * 84)
    print("_p222 六项落地状态")
    print("=" * 84)
    todo = []
    for name, ok in checks:
        print(f"  {'✅' if ok else '🔴'} {name}")
        if not ok:
            todo.append(name)
    print()
    print(f"  完成 {len(checks) - len(todo)}/{len(checks)}")
    for t in todo:
        print(f"    🔴 待做: {t}")

    print()
    print("=" * 84)
    print("当前标题")
    print("=" * 84)
    import re
    m = re.search(r"\\title\{(.*?)\n", mt, re.S)
    print("  " + " ".join(m.group(1).split())[:150] if m else "  (无)")
    print()
    print("=" * 84)
    print("高亮条目")
    print("=" * 84)
    for ln in hl.splitlines():
        if ln.strip().startswith(r"\item"):
            print("  " + ln.strip()[:120])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
