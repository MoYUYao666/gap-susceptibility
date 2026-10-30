# -*- coding: utf-8 -*-
r"""定位 PDF 中残留的旧值，逐处看语境（2026-10-07）。"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
r = subprocess.run(["pdftotext", "-layout", str(REPO / "paper合" / "main_nc.pdf"), "-"],
                   capture_output=True)
t = re.sub(r"\s+", " ", r.stdout.decode("utf-8", "ignore"))

for key in ("0.986", "0.984", "0.985", "162"):
    print("=" * 100)
    print(f"  【{key}】")
    print("=" * 100)
    for m in re.finditer(re.escape(key), t):
        seg = t[max(0, m.start() - 190): m.start() + 130].strip()
        print(f"    …{seg}…")
        print()
