# -*- coding: utf-8 -*-
r"""把新标题同步进 `cover_letter.tex` 与 `declaration.tex`（2026-10-12）。

    python tools\_p232_sync_title.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"
OLD = ("Order Preservation as a Zero-Overhead Monitor for Classification Fine-Tuning: "
       "Why the Modality Gap Is Not a Universal Health Metric")
NEW = ("Order Preservation Tracks Zero-Shot Accuracy under Classification Fine-Tuning: "
       "Why the Modality Gap Is Not a Universal Health Metric")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    files = [A1 / "cover_letter.tex", A1 / "declaration.tex"]
    total = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        # 容忍换行
        flat = t.replace("\n", " ")
        c = flat.count(OLD)
        print(f"  {f.name}: 命中 {c}")
        if c == 0:
            continue
        if not args.apply:
            continue
        # 用"逐词替换"避免换行差异：把 OLD 的每个词边界都允许空白
        import re
        pat = re.compile(r"Order\s+Preservation\s+as\s+a\s+Zero-Overhead\s+Monitor\s+for\s+"
                         r"Classification\s+Fine-Tuning:\s+Why\s+the\s+Modality\s+Gap\s+Is\s+"
                         r"Not\s+a\s+Universal\s+Health\s+Metric")
        t2, n = pat.subn(NEW, t)
        if n == 0:
            # 退化：整段字面替换（含换行）
            t2 = t.replace(OLD, NEW)
            n = t.count(OLD)
        if n == 0:
            print(f"    🔴 未能替换 {f.name}")
            continue
        bak = f.with_suffix(".tex.bak_p232")
        if not bak.exists():
            shutil.copy2(f, bak)
        io.open(f, "w", encoding="utf-8", newline="").write(t2)
        print(f"    ✅ 替换 {n} 处")
        total += n
    if not args.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共 {total} 处")
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        print(f"  复核 {f.name}: 旧 {t.count('Zero-Overhead Monitor')} ｜ "
              f"新 {t.count('Tracks Zero-Shot Accuracy')}")
        assert "Zero-Overhead Monitor" not in t, f"{f.name} 仍有旧标题"
    print("  ✅ 标题已统一")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
