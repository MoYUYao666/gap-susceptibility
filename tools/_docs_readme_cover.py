# -*- coding: utf-8 -*-
r"""给投稿包 README 补「Cover Letter 来源」说明（2026-10-11）。

    python tools\_docs_readme_cover.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "NC_submission" / "README.md"

OLD = "| **投稿包一致性** | `tools/_p190_finish_submission.py` → `latex_source` 与主稿**哈希一致** |"
NEW = ("| **投稿包一致性** | `tools/_p190_finish_submission.py` → `latex_source` 与主稿**哈希一致** |\n"
       "| **Cover Letter 来源** | `paper合/cover_letter.tex`（通用，刊名占位）→ 派生 "
       "`cover_letter_nc.tex`（写死 Neurocomputing）→ 本包 `Cover Letter.pdf`"
       "（`tools/_p197_sync_cover_nc.py`，三者哈希一致） |")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
    if n != 1:
        for i, ln in enumerate(t.splitlines(), 1):
            if "投稿包一致性" in ln:
                print(f"  L{i}: {ln.rstrip()[:130]}")
        return 1
    t2 = t.replace(OLD, NEW, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    assert "Cover Letter 来源" in t3
    print("  ✅ README 已补 Cover Letter 来源说明")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
