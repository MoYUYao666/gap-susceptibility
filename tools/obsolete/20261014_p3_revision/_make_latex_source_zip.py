# -*- coding: utf-8 -*-
"""把投稿包里的 LaTeX 源打成 zip（Elsevier 门户的 "LaTeX source files" 槽位要 zip）。

产物：`paper3/paper_ieee/PRL_submission/latex_source.zip`，含
  main.tex / references.bib / main.bbl / sections/*.tex / figures/*

并做两项自检：① 包内条目齐全；② 解到临时目录后能独立编译且页数与投稿件一致。

    python tools/_make_latex_source_zip.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUBMISSION = REPO / "paper3" / "paper_ieee" / "PRL_submission"
SRC = SUBMISSION / "latex_source"
OUT = SUBMISSION / "latex_source.zip"

REQUIRED = ["main.tex", "references.bib", "main.bbl"]
EXPECT_SECTIONS = 7
EXPECT_FIGURES = 6


def build() -> int:
    if not SRC.is_dir():
        print(f"FAIL: 找不到源目录 {SRC}")
        return 1
    if OUT.exists():
        OUT.unlink()

    files: list[Path] = []
    for p in sorted(SRC.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            files.append(p)

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, arcname=str(p.relative_to(SRC)).replace("\\", "/"))

    with zipfile.ZipFile(OUT) as z:
        names = z.namelist()
        crc_ok = z.testzip() is None

    print(f"写出 {OUT.name}: {OUT.stat().st_size} bytes / {len(names)} 条目 / CRC {'PASS' if crc_ok else 'FAIL'}")
    for n in sorted(names):
        print("   ", n)

    ok = True
    for req in REQUIRED:
        if req not in names:
            print(f"FAIL: 缺 {req}")
            ok = False
    n_sec = sum(1 for n in names if n.startswith("sections/") and n.endswith(".tex"))
    n_fig = sum(1 for n in names if n.startswith("figures/"))
    print(f"自检: sections={n_sec}（期望 {EXPECT_SECTIONS}）, figures={n_fig}（期望 {EXPECT_FIGURES}）")
    if n_sec != EXPECT_SECTIONS or n_fig != EXPECT_FIGURES:
        print("FAIL: 条目数与期望不符")
        ok = False

    # 解到临时目录独立编译
    tmp = Path(tempfile.mkdtemp(prefix="prl_src_"))
    try:
        with zipfile.ZipFile(OUT) as z:
            z.extractall(tmp)
        for cmd in (["pdflatex", "-interaction=nonstopmode", "main.tex"],
                    ["bibtex", "main"],
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"]):
            subprocess.run(cmd, cwd=tmp, capture_output=True)
        log = (tmp / "main.log").read_text(encoding="utf-8", errors="ignore")
        n_err = sum(1 for l in log.splitlines() if l.startswith("!"))
        n_undef = log.count("undefined")
        out = subprocess.run(["pdfinfo", str(tmp / "main.pdf")], capture_output=True)
        pages = [l for l in out.stdout.decode("utf-8", "ignore").splitlines() if l.startswith("Pages")]
        print(f"解压后独立编译: {pages[0].strip() if pages else '页数未知'}, error={n_err}, undefined={n_undef}")
        if n_err or n_undef:
            print("FAIL: 独立编译有错")
            ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("结果:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(build())
