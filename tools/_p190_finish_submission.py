# -*- coding: utf-8 -*-
r"""补完投稿包重建：编译 + 打包 + 核对（修正 GBK 输出解码）（2026-10-11）。

## 上一版崩在哪

`subprocess.run(["pdfinfo", ...], text=True)` 默认按 **UTF-8** 解码，
而本机 `pdfinfo` 对中文错误信息输出 **GBK**（字节 `0xd6`）→ `UnicodeDecodeError`。

**修法**：`encoding="utf-8", errors="replace"`，或直接读 PDF 字节数。

    python tools\_p190_finish_submission.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper合"
PKG = SRC / "NC_submission"
LS = PKG / "latex_source"
SECTIONS = ["empirical.tex", "validation.tex", "supplement.tex", "discussion.tex"]


def sha(p: Path) -> str:
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()[:12]


def run(cmd, cwd) -> int:
    r = subprocess.run(cmd, capture_output=True, cwd=str(cwd))
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0

    print("=== ① 包内编译 main_nc.tex ===")
    run(["pdflatex", "-interaction=nonstopmode", "main_nc.tex"], LS)
    run(["bibtex", "main_nc"], LS)
    run(["pdflatex", "-interaction=nonstopmode", "main_nc.tex"], LS)
    run(["pdflatex", "-interaction=nonstopmode", "main_nc.tex"], LS)

    pdf, log = LS / "main_nc.pdf", LS / "main_nc.log"
    pages = errs = undef = "?"
    if pdf.exists():
        o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                           encoding="utf-8", errors="replace").stdout or ""
        m = re.search(r"Pages:\s+(\d+)", o)
        pages = m.group(1) if m else "?"
    if log.exists():
        t = io.open(log, encoding="utf-8", errors="replace").read()
        errs = len(re.findall(r"^!", t, re.M))
        undef = len(re.findall(r"(Citation|Reference) .* undefined", t))
    print(f"  {pages} 页 ｜ 错误 {errs} ｜ 未定义引用 {undef}")
    if pdf.exists():
        shutil.copy2(pdf, PKG / "Manuscript.pdf")
        print(f"  ✅ Manuscript.pdf 已更新（{pages} 页，"
              f"{(PKG / 'Manuscript.pdf').stat().st_size / 1e6:.2f} MB）")

    print("\n=== ② 重建 latex_source.zip ===")
    zpath = PKG / "latex_source.zip"
    n = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(LS.rglob("*")):
            if f.is_file() and f.suffix.lower() in (".tex", ".bib", ".pdf", ".png",
                                                    ".jpg", ".sty", ".cls"):
                z.write(f, f.relative_to(LS))
                n += 1
    print(f"  ✅ {n} 个文件，{zpath.stat().st_size / 1e6:.2f} MB")

    print("\n=== ③ 核对：包内 == 当前 ===")
    bad = 0
    for x in SECTIONS:
        ok = sha(SRC / "sections" / x) == sha(LS / "sections" / x)
        bad += 0 if ok else 1
        print(f"  {'✅' if ok else '🔴'} {x}")
    for x in ("main_nc.tex", "references.bib"):
        ok = sha(SRC / x) == sha(LS / x)
        bad += 0 if ok else 1
        print(f"  {'✅' if ok else '🔴'} {x}")
    print(f"\n  {'✅ 投稿包已同步' if bad == 0 else f'🔴 {bad} 个不一致'}")
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
