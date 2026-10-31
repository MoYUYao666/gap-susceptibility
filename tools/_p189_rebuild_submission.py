# -*- coding: utf-8 -*-
r"""重建 `paper合/NC_submission/`（投稿包已过期）（2026-10-11）。

## 为什么

投稿包里的 4 个 section 副本停在 10-05/10-06，而它们已在 10-11 大改：
- `empirical.tex`（`tab:position_strict` 3 行 + 表注）
- `validation.tex`（数据集翻转段）
- `supplement.tex`（`tab:vlm` 13 seed）
- `discussion.tex`（Second limitation）

→ `Manuscript.pdf` 与 `latex_source.zip` 都是旧稿。

## 本脚本做

1. **把当前 sections 复制进包**（4 个文件）
2. **在包内就地编译 `main_nc.tex`** → `Manuscript.pdf`（56 页）
3. **重建 `latex_source.zip`**
4. **核对哈希**：包内文件 == 当前文件
5. **报告页数与编译状态**

    python tools\_p189_rebuild_submission.py [--apply]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=== ① 待同步的 sections ===")
    todo = []
    for n in SECTIONS:
        cur, pkg = SRC / "sections" / n, LS / "sections" / n
        if not cur.exists():
            print(f"  ❌ 当前缺 {n}")
            return 1
        same = pkg.exists() and sha(cur) == sha(pkg)
        print(f"  {'✅' if same else '🔴'} {n:<18} 当前 {sha(cur)}"
              + (f" ｜ 包内 {sha(pkg)}" if pkg.exists() else " ｜ 包内缺"))
        if not same:
            todo.append(n)
    print(f"  → 需同步 {len(todo)} 个")

    if not a.apply:
        print("\n  （预演）")
        return 0

    for n in todo:
        shutil.copy2(SRC / "sections" / n, LS / "sections" / n)
    print(f"  ✅ 已复制 {len(todo)} 个 section 到包内")

    # ② 就地编译
    print("\n=== ② 在包内编译 main_nc.tex ===")
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(LS))
    subprocess.run(["bibtex", "main_nc"], capture_output=True, text=True, cwd=str(LS))
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(LS))
    pdf = LS / "main_nc.pdf"
    log = LS / "main_nc.log"
    pages = errs = undef = ""
    if pdf.exists():
        o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", o)
        pages = m.group(1) if m else "?"
    if log.exists():
        t = io.open(log, encoding="utf-8", errors="replace").read()
        errs = len(re.findall(r"^!", t, re.M))
        undef = len(re.findall(r"(Citation|Reference) .* undefined", t))
    print(f"  {pages} 页 ｜ 错误 {errs} ｜ 未定义引用 {undef}")
    if pdf.exists():
        shutil.copy2(pdf, PKG / "Manuscript.pdf")
        print(f"  ✅ Manuscript.pdf 已更新（{pages} 页）")

    # ③ 重建 zip
    print("\n=== ③ 重建 latex_source.zip ===")
    zpath = PKG / "latex_source.zip"
    n_files = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(LS.rglob("*")):
            if f.is_file() and f.suffix.lower() in (".tex", ".bib", ".pdf", ".png",
                                                    ".jpg", ".sty", ".cls"):
                z.write(f, f.relative_to(LS))
                n_files += 1
    print(f"  ✅ latex_source.zip（{n_files} 个文件，{zpath.stat().st_size / 1e6:.2f} MB）")

    # ④ 核对
    print("\n=== ④ 核对：包内 == 当前 ===")
    bad = 0
    for n in SECTIONS:
        ok = sha(SRC / "sections" / n) == sha(LS / "sections" / n)
        if not ok:
            bad += 1
        print(f"  {'✅' if ok else '🔴'} {n}")
    if sha(SRC / "main_nc.tex") != sha(LS / "main_nc.tex"):
        bad += 1
        print("  🔴 main_nc.tex 不一致")
    else:
        print("  ✅ main_nc.tex")
    print(f"\n  {'✅ 投稿包已同步' if bad == 0 else f'🔴 {bad} 个不一致'}")
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
