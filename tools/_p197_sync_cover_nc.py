# -*- coding: utf-8 -*-
r"""从新版通用 cover letter 派生 NC 专用版，并同步进投稿包（2026-10-11）。

## 现状

| 文件 | 状态 |
|---|---|
| `paper合/cover_letter.tex` | ✅ 通用版（`\journal` 占位）——**刚重写** |
| `paper合/cover_letter_nc.tex` | 🔴 **10-02 旧版**（写死 Neurocomputing，含 49 页/patch-size 等过期内容） |
| `NC_submission/Cover Letter.pdf` | 🔴 由旧 NC 版编译（与新版不一致） |

## 做法

1. 从**新版** `cover_letter.tex` 派生 `cover_letter_nc.tex`（把 `\journal` 占位替换为 `Neurocomputing`）
2. 编译 → `cover_letter_nc.pdf`
3. 复制进包 → `Cover Letter.pdf`
4. 核对三者的 PDF 哈希一致

    python tools\_p197_sync_cover_nc.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper合"
PKG = SRC / "NC_submission"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0

    gen = io.open(SRC / "cover_letter.tex", encoding="utf-8", errors="replace").read()
    nc = gen.replace(
        r"\newcommand{\journal}{[TARGET JOURNAL --- replace before submission]}",
        r"\newcommand{\journal}{Neurocomputing}")
    assert "Neurocomputing" in nc, "刊名替换失败"
    assert "[TARGET JOURNAL" not in nc, "占位符仍在"
    io.open(SRC / "cover_letter_nc.tex", "w", encoding="utf-8", newline="").write(nc)
    print("  ✅ cover_letter_nc.tex 已从新版派生（写死 Neurocomputing）")

    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "cover_letter_nc.tex"],
                       capture_output=True, cwd=str(SRC))
    log = SRC / "cover_letter_nc.log"
    errs = 0
    if log.exists():
        t = io.open(log, encoding="utf-8", errors="replace").read()
        errs = len(re.findall(r"^!", t, re.M))
    pdf = SRC / "cover_letter_nc.pdf"
    o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                       encoding="utf-8", errors="replace").stdout or ""
    m = re.search(r"Pages:\s+(\d+)", o)
    print(f"  cover_letter_nc.pdf: {m.group(1) if m else '?'} 页 ｜ 错误 {errs}")

    shutil.copy2(pdf, PKG / "Cover Letter.pdf")
    print("  ✅ Cover Letter.pdf 已更新")

    def sha(p: Path) -> str:
        return hashlib.sha256(io.open(p, "rb").read()).hexdigest()[:12]

    h1, h2 = sha(pdf), sha(PKG / "Cover Letter.pdf")
    print(f"\n  派生版 {h1} ｜ 包内 {h2} ｜ {'✅ 一致' if h1 == h2 else '🔴 不一致'}")
    return 0 if h1 == h2 else 2


if __name__ == "__main__":
    raise SystemExit(main())
