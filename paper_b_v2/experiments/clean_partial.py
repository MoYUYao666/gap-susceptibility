#!/usr/bin/env python3
"""Remove incomplete P1 run JSONs so the matrix can resume safely."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRS = [
    "runs_b32_r6_full",
    "runs_b32_r12_full",
    "runs_b32_r24_full",
    "runs_b32_r48_full",
    "runs_b32_split2_full",
    "runs_siglip_r8_dtd",
    "runs_siglip_r8_other",
]

for name in DIRS:
    d = ROOT / "outputs/paper_b" / name
    if not d.exists():
        continue
    removed = 0
    for p in d.glob("*.json"):
        if p.name == "summary.json":
            continue
        try:
            n = len(json.loads(p.read_text(encoding="utf-8")).get("epochs", []))
        except Exception:
            n = -1
        if n < 3:
            p.unlink()
            removed += 1
    print(f"{name}: removed {removed} incomplete")
