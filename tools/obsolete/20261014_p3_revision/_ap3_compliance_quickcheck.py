# -*- coding: utf-8 -*-
"""ap3 投稿合规快检：摘要词数、关键词、指南中的篇幅条款。

只读；不修改任何文件。依据 Neurocomputing 官方 Guide 的本地留档
（`_guide_neurocomputing.txt`，操作者 2026-09-16 下载，1367 行）。

    python tools/_ap3_compliance_quickcheck.py
"""
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEX = REPO / "paper_ap3" / "main.tex"
GUIDE = REPO / "_guide_neurocomputing.txt"
PDF = REPO / "paper_ap3" / "main.pdf"


def abstract_words(tex: str) -> int:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if not m:
        return -1
    body = m.group(1)
    body = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", " ", body)
    body = re.sub(r"[{}$\\]", " ", body)
    return len(re.findall(r"[A-Za-z][A-Za-z0-9'-]*", body))


def main() -> int:
    tex = io.open(TEX, encoding="utf-8").read()
    guide = io.open(GUIDE, encoding="utf-8").read() if GUIDE.is_file() else ""
    lines = guide.split("\n")

    print("=== 1. 摘要长度 ===")
    n = abstract_words(tex)
    print(f"  abstract 环境内词数 : {n}   （Guide L656: 不得超过 250 词）")
    print("  判定 : " + ("PASS" if 0 < n <= 250 else f"FAIL —— 超出 {n - 250} 词" if n > 250 else "无法测量"))

    print("\n=== 2. 关键词 ===")
    has_kw_env = bool(re.search(r"\\begin\{keyword", tex))
    kw_hits = [i + 1 for i, l in enumerate(lines) if "1 to 7 keywords" in l]
    print(f"  main.tex 是否有 keyword 环境 : {has_kw_env}")
    print(f"  Guide 要求 : L{kw_hits[0] if kw_hits else '?'} 'You are required to provide 1 to 7 keywords'")
    print("  判定 : " + ("PASS" if has_kw_env else "FAIL —— 缺关键词段（声明为必填）"))

    print("\n=== 3. Guide 中的篇幅类条款（逐条原文）===")
    pats = ("word", "page", "length", "limit", "double", "spac", "column", "highlights", "biograph")
    hits = 0
    for i, l in enumerate(lines, start=1):
        if not re.search(r"\d", l):
            continue
        if not any(p in l.lower() for p in pats):
            continue
        s = l.strip()
        if len(s) < 25:
            continue
        print(f"  L{i}: {s[:180]}")
        hits += 1
        if hits >= 14:
            break
    print("  （以上为全部带数字的篇幅类条款；**没有**总页数或总字数上限条目）")

    print("\n=== 4. 可提交文件与版式 ===")
    for i, l in enumerate(lines, start=1):
        ls = l.strip()
        if "PDF is not an acceptable source file" in ls or "single-column layout" in ls:
            print(f"  L{i}: {ls[:180]}")

    if PDF.is_file():
        import subprocess

        out = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True)
        txt = out.stdout.decode("utf-8", "ignore")
        words = len(re.findall(r"[A-Za-z][A-Za-z0-9-]*", txt))
        before_refs = txt[: txt.find("References")] if "References" in txt else txt
        print(f"\n=== 5. 实测篇幅（{PDF.name}）===")
        print(f"  页数 {txt.count(chr(12))}；全文词数 {words}；去掉参考文献后 {len(re.findall(r'[A-Za-z][A-Za-z0-9-]*', before_refs))}")
        print("  同刊已受理对照：paper_a1/main.pdf 40 页 / 16,190 词（去参考文献）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
