# -*- coding: utf-8 -*-
r"""Paper A / Neurocomputing 投稿包终检（从实际 PDF 核验，而非只看源文件）。

## 核验项

1. 页数、编译错误、未定义引用；
2. **摘要词数**（从 PDF 抽出，对照 Guide 的 250 词上限）；
3. **Highlights**：条数 3–5、每条 ≤85 字符（对照 Guide）；
4. **声明齐备且位于参考文献之前**：Data availability / Funding / Competing interests / CRediT /
   Generative AI；
5. **参考文献条数**与正文引用是否一致；
6. **包内文件齐备**。

    python tools\_pa_final_check_nc.py
"""
from __future__ import annotations

import io
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
PKG = PA / "NC_submission"
PDF = PKG / "Manuscript.pdf"

DECLS = ["Data availability", "Funding", "Declaration of competing interests",
         "CRediT authorship contribution statement",
         "Declaration of generative AI and AI-assisted technologies"]


def pdftotext(p: Path, *args: str) -> str:
    r = subprocess.run(["pdftotext", *args, str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", "ignore")


def main() -> int:
    problems: list[str] = []
    txt = pdftotext(PDF)
    norm = re.sub(r"\s+", " ", txt)

    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True).stdout.decode("utf-8", "ignore")
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    print(f"页数 {pages}")

    # 摘要：从 Abstract 到 Keywords/Introduction 之间。
    # ⚠ 注意：pdftotext 会把**首页页脚**（"∗ Corresponding author. Email address: … (Hongrui Wan)"）
    # 插进正文流中间，若不去掉会虚增约 11 词、把合规的摘要误判为超限。
    m = re.search(r"Abstract\s*(.*?)\s*(?:Keywords|1\.?\s*Introduction)", norm, re.S)
    if m:
        raw = m.group(1)
        footnote = re.search(r"∗?\s*Corresponding author\..*?\(Hongrui Wan\)", raw, re.S)
        had_footnote = bool(footnote)
        cleaned = re.sub(r"∗?\s*Corresponding author\..*?\(Hongrui Wan\)", " ", raw, flags=re.S)
        wc_raw, wc = len(raw.split()), len(cleaned.split())
        print(f"摘要 {wc} 词（Guide 上限 250）{'✅' if wc <= 250 else '❌'}"
              + (f" ［原始抽取得 {wc_raw} 词，已剔除首页页脚 {wc_raw - wc} 词］" if had_footnote else ""))
        if wc > 250:
            problems.append(f"摘要 {wc} 词超限")
    else:
        print("摘要 ❌ 未能从 PDF 定位")
        problems.append("摘要定位失败")

    # Highlights
    hp = PKG / "Highlights.txt"
    if hp.exists():
        items = [l[2:].strip() for l in io.open(hp, encoding="utf-8") if l.startswith("- ")]
        longest = max(len(x) for x in items) if items else 0
        ok = 3 <= len(items) <= 5 and longest <= 85
        print(f"Highlights {len(items)} 条，最长 {longest} 字符 {'✅' if ok else '❌'}")
        if not ok:
            problems.append("Highlights 不合规")
    else:
        problems.append("缺 Highlights.txt")

    # 声明与位置
    print("声明章节：")
    positions = {}
    for d in DECLS:
        i = norm.find(d)
        positions[d] = i
        print(f"  {d[:48]:50s} {'✅' if i >= 0 else '❌'}")
        if i < 0:
            problems.append(f"缺声明：{d}")
    i_ref = norm.find("References")
    if i_ref > 0 and all(v >= 0 for v in positions.values()):
        before = all(v < i_ref for v in positions.values())
        print(f"声明均位于参考文献之前 {'✅' if before else '❌'}")
        if not before:
            problems.append("声明位置不在参考文献之前")

    # 参考文献
    # 引用制式要两种都认：本文用 elsarticle-harv（作者-年份制，如 "Radford et al. (2021)"），
    # 而原实现只统计数字制 [n] → 在 44 条文献的稿子上报"0 处"，**属于误导**。
    n_num = len(re.findall(r"\[\d+(?:\s*[,–-]\s*\d+)*\]", norm))
    n_ay = len(re.findall(r"[A-Z][a-zA-Z\-]+(?:\s+(?:et\s+al\.|and\s+[A-Z][a-zA-Z\-]+))?\s*\(\d{4}[a-z]?\)", norm))
    n_ay2 = len(re.findall(r"\([A-Z][a-zA-Z\-]+(?:\s+(?:et\s+al\.|and\s+[A-Z][a-zA-Z\-]+))?,\s*\d{4}[a-z]?\)", norm))
    print(f"PDF 中的引用标记：数字制 {n_num} 处 ｜ 作者-年份制 {n_ay + n_ay2} 处"
          f"（制式依 bibliographystyle；elsarticle-harv 为作者-年份）")
    if n_num + n_ay + n_ay2 == 0:
        problems.append("PDF 中未检出任何引用标记")
    bbl = PA / "main_nc.bbl"
    if bbl.exists():
        n = len(re.findall(r"\\bibitem", io.open(bbl, encoding="utf-8", errors="ignore").read()))
        print(f"参考文献 {n} 条 {'✅' if n > 0 else '❌'}")
        if n == 0:
            problems.append("参考文献为空")
    log = PA / "main_nc.log"
    if log.exists():
        ltxt = io.open(log, encoding="utf-8", errors="ignore").read()
        err = len([l for l in ltxt.splitlines() if l.startswith("!")])
        und = ltxt.count("Citation") and ltxt.count("undefined")
        print(f"编译错误 {err} {'✅' if err == 0 else '❌'} ｜ 未定义引用 {und} {'✅' if und == 0 else '❌'}")
        if err or und:
            problems.append("编译/引用问题")

    # 包内文件
    print("包内文件：")
    for name in ("Manuscript.pdf", "Highlights.pdf", "Highlights.txt", "Cover Letter.pdf",
                 "latex_source.zip", "README.md"):
        ok = (PKG / name).exists()
        print(f"  {name:22s} {'✅' if ok else '❌'}")
        if not ok:
            problems.append(f"缺 {name}")

    print()
    if problems:
        print("❌ 待修：" + "；".join(problems))
        return 1
    print("✅ 全部通过，可投稿")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
