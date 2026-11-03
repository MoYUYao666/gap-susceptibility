# -*- coding: utf-8 -*-
r"""Enforce the no-underscore submission filename rule in the venue package builder.

    python tools/_p1490_no_underscore_filenames.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(REPO, "tools", "_p1336_build_venue_package.py")
REBUILD = os.path.join(REPO, "tools", "_p1445_rebuild_packages.py")
RULE = """

## 🔴🔴 投稿文件名规则（2026-10-21 立，长期有效）

> 操作者原话："所有投搞的文件名称不要有 '_'"

- **适用范围**：所有向期刊/会议系统上传的文件名（Manuscript、Supplementary、CoverLetter、TitlePage、Abstract、
  Highlights、LaTeXSource 等），**一律不含下划线**；用驼峰（`CoverLetter.pdf`）或连字符。
- 实现：`tools/_p1336_build_venue_package.py` 统一重命名为 `Manuscript.pdf`、`Supplementary.pdf`、
  `CoverLetter.pdf`、`TitlePage.pdf`、`Abstract.pdf`、`Highlights.pdf`、`LaTeXSource.zip`；
  `tools/_p1445_rebuild_packages.py` 重建时自动生效。
- 本地源文件/脚本名不受此规则约束（只在**上传文件名**层面执行）。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(BUILDER, encoding="utf-8").read()
    changed = False
    if "TitlePage.pdf" not in t:
        t = t.replace(
            '    for name, rel in (("title_page", a.title_page), ("cover_letter", a.cover_letter),\n'
            '                      ("abstract", a.abstract), ("highlights", a.highlights)):\n'
            '        if rel:\n'
            '            items.append((name, abs_(rel), os.path.basename(rel)))',
            '    targets = {"title_page": "TitlePage.pdf", "cover_letter": "CoverLetter.pdf",\n'
            '               "abstract": "Abstract.pdf", "highlights": "Highlights.pdf"}\n'
            '    for name, rel in (("title_page", a.title_page), ("cover_letter", a.cover_letter),\n'
            '                      ("abstract", a.abstract), ("highlights", a.highlights)):\n'
            '        if rel:\n'
            '            items.append((name, abs_(rel), targets[name]))', 1)
        t = t.replace('zpath = os.path.join(out, "latex_source.zip")',
                      'zpath = os.path.join(out, "LaTeXSource.zip")', 1)
        t = t.replace("| LaTeX source | `latex_source.zip` | {n_source} files |",
                      "| LaTeX source | `LaTeXSource.zip` | {n_source} files |", 1)
        changed = True
        print("  builder updated for underscore-free names")
    if a.apply and changed:
        io.open(BUILDER, "w", encoding="utf-8", newline="").write(t)
        print("  written")
    # record the rule in the workspace instruction files
    if a.apply:
        for f in ("AGENTS.md", "CLAUDE.md"):
            p = os.path.join(REPO, f)
            if os.path.exists(p):
                x = io.open(p, encoding="utf-8").read()
                if "投稿文件名规则（2026-10-21 立" not in x:
                    io.open(p, "w", encoding="utf-8", newline="").write(x.rstrip() + RULE)
                    print("  rule appended to", f)
        r = subprocess.run([sys.executable, REBUILD, "--apply"], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        print((r.stdout or "")[-500:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
