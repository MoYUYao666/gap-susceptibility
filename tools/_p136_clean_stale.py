# -*- coding: utf-8 -*-
r"""清除 A1 遗留的旧刊名/旧标题（2026-10-10）。

`tools/_p135` 查出：
- `main.tex` 残留 `Neurocomputing` ×1
- `abstract.tex` 残留旧标题 ×1 + `Neurocomputing` ×1

    python tools\_p136_clean_stale.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"

OLD_TITLE = "The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness"
NEW_TITLE = ("Order Preservation as a Zero-Overhead Monitor for Classification Fine-Tuning: "
             "Why the Modality Gap Is Not a Universal Health Metric")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for name in ("main.tex", "abstract.tex"):
        f = A1 / name
        if not f.exists():
            continue
        t = io.open(f, encoding="utf-8", errors="replace").read()
        print(f"\n{'=' * 62}\n{name}\n{'=' * 62}")
        for pat in ("Neurocomputing", OLD_TITLE):
            for m in re.finditer(re.escape(pat), t):
                ctx = " ".join(t[max(0, m.start() - 170):m.start() + 130].split())
                print(f"  [{pat[:24]}…] …{ctx}…")
        n_nt = t.count(OLD_TITLE)
        n_nc = t.count("Neurocomputing")
        print(f"  → 旧标题 {n_nt} 处 ｜ 旧刊名 {n_nc} 处")

        if a.apply and (n_nt or n_nc):
            t2 = t.replace(OLD_TITLE, NEW_TITLE)
            # 刊名：仅替换"投给 Neurocomputing"这类描述为中性/新刊
            t2 = re.sub(r"(?:submitted to|for consideration in|in)\s+\\?textit\{Neurocomputing\}",
                        "", t2)
            t2 = t2.replace("Neurocomputing", "Neural Networks")
            io.open(f, "w", encoding="utf-8", newline="").write(t2)
            print(f"  ✅ 已清（标题 {n_nt}｜刊名 {n_nc}）")

    if a.apply:
        print("\n=== 复核 ===")
        for name in ("main.tex", "abstract.tex"):
            t = io.open(A1 / name, encoding="utf-8", errors="replace").read()
            print(f"  {name:<14} 旧标题 {t.count(OLD_TITLE)} ｜ 旧刊名 {t.count('Neurocomputing')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
