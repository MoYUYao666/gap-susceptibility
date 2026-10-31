# -*- coding: utf-8 -*-
r"""核实 A1 会话加固项的准确计数（2026-10-10）。

## 要查

1. **limitation 到底几条**——我数出 12 个序数词但含重复，说明统计串了别的段；
2. **补充材料是几节、节名是什么**——我的正则没匹配上。

    python tools\_p139_verify_counts.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    d = REPO / "paper合" / "sections" / "discussion.tex"
    t = io.open(d, encoding="utf-8", errors="replace").read()

    print("=== limitation 段范围 ===")
    i = t.find("Several limitations")
    j = t.find("Several extensions")
    if i < 0:
        i = t.find("limitations of this work")
    print(f"  起点 {i} ｜ 终点 {j}")
    seg = t[i:j] if (i >= 0 and j > i) else ""
    print(f"  段长 {len(seg)} 字符")

    m = re.findall(r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)\b,", seg)
    print(f"\n=== limitation 序数词（段内）：{len(m)} 个 ===")
    print("  ", m)
    nums = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth",
            "Seventh", "Eighth", "Ninth", "Tenth"]
    print(f"  顺序正确: {'✅' if m == nums[:len(m)] else '❌'}")
    if m != nums[:len(m)]:
        print("   实际:", m)
        print("   应为:", nums[:len(m)])

    # 全文里的序数词（说明为何我数出 12）
    allm = re.findall(r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)\b,",
                      t)
    print(f"\n  全文序数词总数 {len(allm)}（我先前数出 12 是因为统计串了段外内容）")
    print("  ", allm)

    print("\n=== 补充材料节 ===")
    s = REPO / "paper合" / "sections" / "supplement.tex"
    st = io.open(s, encoding="utf-8", errors="replace").read()
    print(f"  文件 {len(st.splitlines())} 行")
    secs = re.findall(r"\\(?:section|subsection)\*?\{([^}]*)\}", st)
    print(f"  节标题 {len(secs)} 个：")
    for x in secs:
        print("   •", x[:80])
    print(f"\n  含 'Monte-Carlo'/'signal-to-noise': "
          f"{'✅' if 'signal-to-noise' in st or 'Monte-Carlo' in st else '❌'}")
    for k in ("signal-to-noise", "Monte-Carlo", "paired", "deterministic"):
        print(f"    {k}: {'✅' if k in st else '❌'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
