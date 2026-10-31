# -*- coding: utf-8 -*-
r"""PRL 稿件最终校验：页数、摘要/门户字段一致性、裸 markdown 残留、图表引用、引用完整性。

    python tools/_final_check_prl.py
"""
from __future__ import annotations

import io
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl"
PDF = OUT / "main_prl.pdf"
EM = OUT / "UPLOAD" / "EM_fields.txt"
MD = OUT / "MANUSCRIPT.md"
REFS = OUT / "refs_all.json"   # reference pool copied into the live Commentary tree (2026-10-25)


def main() -> int:
    problems: list[str] = []

    # 1) PDF 基本量
    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True).stdout.decode("utf-8", "ignore")
    m = re.search(r"Pages:\s+(\d+)", info)
    pages = int(m.group(1)) if m else -1

    # .log 是编译中间件，可能已被清理（本仓库有清理中间件的习惯）。
    # 缺失时**现场重新编译一次**再读，避免"干净目录上闸门直接崩"。
    logfile = OUT / "main_prl.log"
    if not logfile.exists():
        print("（未找到 main_prl.log，现场重编译一次…）")
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main_prl.tex"],
                       cwd=OUT, capture_output=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main_prl.tex"],
                       cwd=OUT, capture_output=True)
    if logfile.exists():
        log = logfile.read_text(encoding="utf-8", errors="ignore")
        errors = [l for l in log.splitlines() if l.startswith("!")]
        undef = log.count("Citation") and log.count("undefined")
        src = "log"
    else:
        errors, undef, src = ["<无法取得>"], 0, "PDF 直查"
        problems.append("编译日志缺失且重编译失败")
    print(f"页数 {pages} / 7 {'✅' if pages <= 7 else '❌'}")
    if pages > 7:
        problems.append("页数超限")
    print(f"编译错误 {len(errors)} {'✅' if not errors else '❌'}（来源：{src}）")
    print(f"未定义引用 {undef} {'✅' if undef == 0 else '❌'}")
    if undef:
        problems.append("未定义引用")

    pdf = subprocess.run(["pdftotext", "-raw", str(PDF), "-"], capture_output=True).stdout.decode("utf-8", "ignore")
    pdfn = re.sub(r"\s+", " ", pdf)

    # 1b) 未定义引用的直接证据：PDF 里出现 "?" 形式的引用标记
    # （natbib 未解析时渲染为 `[?]` 或 `?`）
    qmarks = len(re.findall(r"\[\?\]|\(\?\)", pdfn))
    print(f"PDF 中未解析引用标记 [?] {qmarks} {'✅' if qmarks == 0 else '❌'}")
    if qmarks:
        problems.append("PDF 中存在未解析引用标记")

    # 2) 裸 markdown 残留
    stars = re.findall(r"\S{0,30}\*\S{0,30}", pdfn)
    print(f"裸 markdown 星号 {len(stars)} {'✅' if not stars else '❌ ' + str(stars[:3])}")
    if stars:
        problems.append("PDF 中残留 markdown 星号")

    # 3) 摘要与门户字段一致
    em_txt = EM.read_text(encoding="utf-8")
    em_title = re.search(r"=== Your title ===\n(.+)", em_txt).group(1).strip()
    em_abs = re.search(r"=== Your abstract ===[^\n]*\n(.+?)\n\n", em_txt, re.S).group(1).strip()
    t_ok = em_title[:60] in pdfn
    a_ok = re.sub(r"\s+", " ", em_abs)[:120] in pdfn
    print(f"门户标题与 PDF 一致 {'✅' if t_ok else '❌'}")
    print(f"门户摘要与 PDF 一致 {'✅' if a_ok else '❌'}")
    if not (t_ok and a_ok):
        problems.append("门户字段与 PDF 不一致")
    n_abs = len(em_abs.split())
    print(f"摘要 {n_abs} 词 / 250 {'✅' if n_abs <= 250 else '❌'}")

    # 4) 图表引用
    tex = (OUT / "main_prl.tex").read_text(encoding="utf-8")
    has_fig = "fig1_decision_space" in tex
    fig_ref = "Figure 1" in pdfn or "Figure~1" in tex
    print(f"含图 {'✅' if has_fig else '❌'} ｜ 正文引用图 {'✅' if fig_ref else '❌'}")
    if has_fig and not fig_ref:
        problems.append("图未被正文引用")

    # 5) 引用完整性
    refs = {e.get("key") for e in json.loads(REFS.read_text(encoding="utf-8"))}
    keys = {k.strip() for m in re.finditer(r"\\cite\{([^}]+)\}", tex) for k in m.group(1).split(",")}
    missing = sorted(keys - refs)
    print(f"正文引用 {len(keys)} 条 ｜ 库中缺失 {len(missing)} {'✅' if not missing else '❌ ' + str(missing)}")
    if missing:
        problems.append("引用键不在库中")
    self_cite = [k for k in keys if k in {"wan2026protect"}]
    print(f"自引 {'✅ 无' if not self_cite else '❌ ' + str(self_cite)}")

    # 6) 2026-10-18 audit blind spots (the checks the old gate missed)
    if logfile.exists():
        log = logfile.read_text(encoding="utf-8", errors="ignore")
        over = len(re.findall(r"Overfull \\hbox", log))
        print(f"Overfull hbox {over} {'OK' if over == 0 else 'FAIL'}")
        if over:
            problems.append("Overfull hbox")

    dbl = re.findall(r"(?m)^\s*\d+(?:\.\d+)*\.\s+\d+(?:\.\d+)*\.\s", pdf)
    print(f"double-numbered headings {len(dbl)} {'OK' if not dbl else 'FAIL ' + str(dbl[:2])}")
    if dbl:
        problems.append("double-numbered headings")

    # The checklist flows across a two-column spread, so the layout text interleaves the
    # columns. Use the flattened text and look for the consecutive run 1..12 inside section 4.
    a2 = pdfn.find("A reporting checklist")
    if a2 < 0:
        a2 = pdfn.find("reporting checklist")
    b2 = pdfn.find("Two remarks", a2 if a2 >= 0 else 0)
    seg2 = pdfn[a2:b2] if a2 >= 0 and b2 > a2 else pdfn
    nums = [int(n) for n in re.findall(r"(?<![\d.])(\d{1,2})\.\s", seg2)]
    # the checklist spans a two-column spread; text extraction can interleave one extra number, so accept the
    # longest strictly increasing subsequence containing 1..12 in order rather than an exact contiguous run
    def lis(seq):
        best = [1] * len(seq)
        prev = [-1] * len(seq)
        for i in range(len(seq)):
            for j in range(i):
                if seq[j] < seq[i] and best[j] + 1 > best[i]:
                    best[i], prev[i] = best[j] + 1, j
        if not seq:
            return []
        k = max(range(len(seq)), key=lambda i: best[i])
        out = []
        while k >= 0:
            out.append(seq[k])
            k = prev[k]
        return list(reversed(out))
    _l = lis(nums)
    run = list(range(1, 13))
    ordered = any(_l[i:i + 12] == run for i in range(max(0, len(_l) - 11)))
    print(f"section 4 checklist numbering {'OK 1..12' if ordered else 'FAIL ' + str(nums[:24])}")
    if not ordered:
        problems.append("section 4 checklist is not 1..12")

    bad = [k for k in ("<scp>", "&amp;", "ORCID(s)") if k in pdf]
    print(f"HTML/XML artifacts {len(bad)} {'OK' if not bad else 'FAIL ' + str(bad)}")
    if bad:
        problems.append("HTML/XML artifacts")

    di = pdfn.find("Declaration")
    ri = pdfn.rfind("References")
    print(f"declarations before references {'OK' if 0 <= di < ri else 'FAIL'}")
    if not (0 <= di < ri):
        problems.append("declarations missing or after references")

    title = re.search(r"\\title\{([^{}]*)\}", tex)
    if title:
        tt = re.sub(r"\s+", " ", title.group(1)).strip()
        clf = re.sub(r"\s+", " ", (OUT / "cover_letter.tex").read_text(encoding="utf-8"))
        ok_title = tt[:50] in clf
        print(f"cover-letter title matches manuscript {'OK' if ok_title else 'FAIL'}")
        if not ok_title:
            problems.append("cover-letter title mismatch")

    print()
    if problems:
        print("❌ 待修：", problems)
        return 1
    print("✅ 全部通过，可投稿")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
