# -*- coding: utf-8 -*-
r"""查论文里是否还有残留的旧解码器 VLM 主张（2026-10-10）。

    python tools\_p160_check_stale_vlm.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

STALE = [
    (r"\$11\\?%\$", "旧 vision_only 11%"),
    (r"83\.8", "旧 both 83.8%"),
    (r"73\.9", "旧 text_only 73.9%"),
    (r"11\.0\\?%", "旧 11.0%"),
    (r"four-bit quantisation, one seed", "旧表注 one seed"),
    (r"0\.636 \\to 0\.103", "旧表行"),
    (r"2\.176 \\to 1\.937", "旧表行"),
    (r"not completed a single epoch after \$27\$", "旧'bf16 不可行'表述"),
    (r"reduces the gap most", "旧'both 最好'主张"),
    (r"least effective choice", "旧'vision 最差'主张"),
]


def main() -> int:
    print("=" * 72)
    print("残留检查")
    print("=" * 72)
    bad = 0
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for pat, tag in STALE:
            for m in re.finditer(pat, t):
                s = " ".join(t[max(0, m.start() - 130):m.start() + 130].split())
                print(f"  ⚠️ [{Path(f).name}] {tag}")
                print(f"      …{s}…")
                bad += 1
    print(f"\n  残留命中: {bad}")
    if bad == 0:
        print("  ✅ 无残留")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
