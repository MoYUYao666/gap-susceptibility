# -*- coding: utf-8 -*-
"""PRL 投稿包审核：逐件比对"源文件 ↔ 投递 PDF"，抓陈旧文件与事实不一致。

审核项：
  1. 每个 PDF 是否可由包内/工程内的源**逐字符重建**（文本级等价）
  2. 稿件关键事实（作者、A800/4060、声明顺序、页数）
  3. highlights 三格式一致性与字符上限
  4. 边界检查：包内不得出现稿件/私密件的误入

    python tools/_audit_prl_package.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "paper3" / "paper_ieee" / "PRL_submission"
PROJ = REPO / "paper3" / "paper_ieee"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


def pdf_text(p: Path) -> str:
    """读 PDF 文本；文件不存在时**硬失败**，不返回空串。

    早期版本对不存在的路径静默返回 ""，导致"找不到产物"被误报成"文本不一致"
    （表现为 '0 vs 3230 字符'）。此处改为显式报错，避免同类掩盖。
    """
    if not p.exists():
        raise FileNotFoundError(f"待比对/比对的 PDF 不存在: {p}")
    out = subprocess.run(["pdftotext", "-raw", str(p), "-"], capture_output=True)
    text = out.stdout.decode("utf-8", "ignore")
    if out.returncode != 0 and not text.strip():
        raise RuntimeError(f"pdftotext 失败（rc={out.returncode}）: {p}")
    return "".join(text.split())


def compile_in(tex: str, workdir: Path, extra_bib: bool = False) -> Path | None:
    """在 workdir 编译 tex，返回产物路径（不存在则 None）。

    注意：tex 为**纯文件名**（如 "cover_letter_prl.tex"），产物即 workdir 下的同名 .pdf。
    早期版本误用 `workdir / tex.replace(".tex", ".pdf")`，在 workdir 为 Path 时会拼成
    嵌套路径 `workdir/cover_letter_prl.tex/cover_letter_prl.pdf`，永远查不到 → 静默失败。
    """
    workdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", tex], cwd=workdir, capture_output=True)
    if extra_bib:
        subprocess.run(["bibtex", tex.replace(".tex", "")], cwd=workdir, capture_output=True)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex], cwd=workdir, capture_output=True)
    pdf = workdir / (tex[:-4] + ".pdf" if tex.endswith(".tex") else tex + ".pdf")
    if not pdf.exists():
        log = workdir / (tex[:-4] + ".log" if tex.endswith(".tex") else tex + ".log")
        detail = ""
        if log.exists():
            errs = [l for l in log.read_text(encoding="utf-8", errors="ignore").splitlines() if l.startswith("!")]
            detail = "；日志首个错误: " + (errs[0][:120] if errs else "（无 '!' 行）")
        print(f"  [debug] 编译未产出 {pdf.name}{detail}")
        return None
    return pdf


def find_pdf(keywords: list[str]) -> Path:
    """在投稿包里按关键词**模糊**定位 PDF（忽略大小写、下划线、空格）。

    投稿门户会把文件显示成 "Cover letter.pdf" / "Title page with declarations.pdf" 之类的名字，
    操作者可能照抄重命名，因此审核脚本不能依赖硬编码文件名。
    """
    norm = lambda s: re.sub(r"[\s_\-]+", "", s.lower())
    cands = [p for p in PKG.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
    for p in cands:
        n = norm(p.name)
        if all(norm(k) in n for k in keywords):
            return p
    raise FileNotFoundError(f"包内未找到匹配 {keywords} 的 PDF；现有: {[p.name for p in cands]}")


def main() -> int:
    # ---------- 1. 逐件源↔PDF 等价 ----------
    tmp = Path(tempfile.mkdtemp(prefix="prl_audit_"))
    try:
        # manuscript.pdf  ← main.pdf（工程编译产物，与 zip 源同源）
        a = pdf_text(find_pdf(["manuscript"]))
        b = pdf_text(PROJ / "main.pdf")
        check("manuscript.pdf 与工程 main.pdf 文本一致", a == b, f"{len(a)} vs {len(b)} 字符")

        # Cover letter.pdf ← cover_letter_prl.tex
        work = tmp / "cover"
        work.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJ / "cover_letter_prl.tex", work / "cover_letter_prl.tex")
        pdf = compile_in("cover_letter_prl.tex", work)
        if pdf:
            x, y = pdf_text(find_pdf(["cover", "letter"])), pdf_text(pdf)
            check("Cover letter 可由 cover_letter_prl.tex 重建", x == y, f"{len(x)} vs {len(y)} 字符")
        else:
            check("cover_letter_prl.tex 可编译", False, "编译未产出 PDF")

        # Title page with declarations.pdf ← title_page_prl.tex
        work = tmp / "title"
        work.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJ / "title_page_prl.tex", work / "title_page_prl.tex")
        pdf = compile_in("title_page_prl.tex", work)
        if pdf:
            x, y = pdf_text(find_pdf(["title", "page"])), pdf_text(pdf)
            check("Title page 可由 title_page_prl.tex 重建", x == y, f"{len(x)} vs {len(y)} 字符")
        else:
            check("title_page_prl.tex 可编译", False, "编译未产出 PDF")

        # highlights.pdf ← highlights.tex
        shutil.copy(PKG / "highlights.tex", tmp / "highlights.tex")
        pdf = compile_in("highlights.tex", tmp)
        if pdf:
            x, y = pdf_text(PKG / "highlights.pdf"), pdf_text(pdf)
            check("highlights.pdf 可由 highlights.tex 重建", x == y, f"{len(x)} vs {len(y)} 字符")
        else:
            check("highlights.tex 可编译", False, "编译未产出 PDF")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---------- 2. 稿件事实 ----------
    main_txt = pdf_text(PKG / "manuscript.pdf")
    info = subprocess.run(["pdfinfo", str(PKG / "manuscript.pdf")], capture_output=True).stdout.decode("utf-8", "ignore")
    n_pages = int([l.split(":")[1] for l in info.splitlines() if l.startswith("Pages")][0].strip())
    check("manuscript 页数 = 11", n_pages == 11, f"实际 {n_pages}")
    check("署名在稿内", "HongruiWan" in main_txt and "Southampton" in main_txt)
    check("无匿名残留", "Suppressed" not in main_txt and "Double-Anonymous" not in main_txt)
    check("致谢硬件 = A800 + RTX 4060（无 4080）",
          "A800" in main_txt and "RTX4060" in main_txt and "4080" not in main_txt)
    order = [main_txt.find("DECLARATIONOFCOMPETING"), main_txt.find("FUNDINGSOURCES"),
             main_txt.find("DECLARATIONOFGENERATIVE"), main_txt.find("DATASTATEMENT"),
             main_txt.find("REFERENCES")]
    check("四项声明齐备且都在 REFERENCES 之前",
          all(i >= 0 for i in order[:-1]) and max(order[:-1]) < order[-1],
          f"偏移 {order}")
    check("无 TNNLS 字样的正文残留", "TNNLS" not in main_txt, "（title page 与封面信可提及，正文不应有）")

    # ---------- 3. highlights ----------
    txt = (PKG / "highlights.txt").read_text(encoding="utf-8")
    bullets = [l[2:] for l in txt.splitlines() if l.startswith("- ")]
    check("highlights 条数 3–5", 3 <= len(bullets) <= 5, f"{len(bullets)} 条")
    longest = max(len(b) for b in bullets)
    check("highlights 每条 ≤85 字符", longest <= 85, f"最长 {longest}")
    hl_pdf = pdf_text(PKG / "highlights.pdf")
    check("highlights.pdf 含全部 5 条", all("".join(b.split()) in hl_pdf for b in bullets))
    import zipfile
    with zipfile.ZipFile(PKG / "highlights.docx") as z:
        doc = z.read("word/document.xml").decode("utf-8")
    check("highlights.docx 含全部 5 条", all("".join(b.split()) in "".join(doc.split()) for b in bullets))

    # ---------- 4. 边界 ----------
    with zipfile.ZipFile(PKG / "latex_source.zip") as z:
        names = z.namelist()
        crc = z.testzip() is None
    check("latex_source.zip CRC 完好", crc)
    check("zip 无编译中间件", not any(n.endswith((".aux", ".log", ".out", ".fls", ".fdb_latexmk")) for n in names),
          f"{len(names)} 条目")
    check("zip 含 sections 与 figures",
          any(n.startswith("sections/") for n in names) and any(n.startswith("figures/") for n in names))
    pkg_files = [p.name for p in PKG.iterdir() if p.is_file()]
    norm = lambda s: re.sub(r"[\s_\-]+", "", s.lower())
    banned = ["title_page.docx", "cover_letter.docx", "conflict.docx", "main_submission.zip", "Reviewer.pdf"]
    offenders = [f for f in pkg_files if any(norm(b) == norm(f) for b in banned)]
    check("包内无 TNNLS 时代旧件（docx 旧件/旧 zip）", not offenders, f"命中: {offenders}" if offenders else "")

    # ---------- 报告 ----------
    print("=" * 72)
    print("PRL 投稿包审核报告")
    print("=" * 72)
    bad = 0
    for name, ok, detail in results:
        flag = "PASS" if ok else "FAIL"
        if not ok:
            bad += 1
        print(f"  [{flag}] {name}" + (f"  ({detail})" if detail else ""))
    print("-" * 72)
    print(f"合计 {len(results)} 项，通过 {len(results) - bad}，失败 {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
